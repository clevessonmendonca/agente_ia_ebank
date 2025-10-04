import { Position } from 'reactflow';

// Função para gerar os nós e arestas a partir do fluxo JSON
export const generateNodesAndEdges = (flowData) => {
    if (!flowData || !flowData.menus) {
        return { nodes: [], edges: [] };
    }

    const nodes = [];
    const edges = [];
    const menuIds = Object.keys(flowData.menus);

    // Posicionamento automático dos nós
    const menuPositions = calculateNodePositions(flowData.menus);

    // Criar nós para cada menu
    menuIds.forEach((menuId) => {
        const menuData = flowData.menus[menuId];
        const position = menuPositions[menuId] || { x: 0, y: 0 };

        nodes.push({
            id: menuId,
            type: 'menuNode',
            position,
            data: {
                menuId,
                menuData,
            },
        });
    });

    // Criar arestas com base nas conexões de próximo menu
    menuIds.forEach((menuId) => {
        const menuData = flowData.menus[menuId];
        const options = menuData.options || {};

        // Conexões para botões
        if (options.menu_type === 'button' && options.buttons) {
            options.buttons.forEach((button, index) => {
                if (button.next_menu && flowData.menus[button.next_menu]) {
                    edges.push({
                        id: `e-${menuId}-${button.next_menu}-${index}`,
                        source: menuId,
                        target: button.next_menu,
                        animated: true,
                        label: button.title,
                        labelStyle: { fontSize: '10px' },
                        labelBgStyle: { fill: '#f0f0f0', fillOpacity: 0.7 },
                    });
                }
            });
        }

        // Conexões para listas
        if (options.menu_type === 'list' && options.sections) {
            options.sections.forEach((section) => {
                if (section.rows) {
                    section.rows.forEach((row, index) => {
                        if (row.next_menu && flowData.menus[row.next_menu]) {
                            edges.push({
                                id: `e-${menuId}-${row.next_menu}-${index}`,
                                source: menuId,
                                target: row.next_menu,
                                animated: true,
                                label: row.title,
                                labelStyle: { fontSize: '10px' },
                                labelBgStyle: {
                                    fill: '#f0f0f0',
                                    fillOpacity: 0.7,
                                },
                            });
                        }
                    });
                }
            });
        }
    });

    return { nodes, edges };
};

// Função para calcular posições automáticas dos nós
const calculateNodePositions = (menus) => {
    const positions = {};
    const menuIds = Object.keys(menus);

    // Encontrar menus iniciais (como menu de privacidade e inicial)
    const rootMenus = menuIds.filter(
        (menuId) => menuId === 'privacidade' || menuId === 'inicial'
    );

    // Construir grafo de dependências
    const graph = buildDependencyGraph(menus);

    // Atribuir níveis aos nós com base na distância dos menus iniciais
    const levels = calculateNodeLevels(graph, rootMenus);

    // Calculor a largura de cada nível
    const levelWidths = {};
    Object.entries(levels).forEach(([menuId, level]) => {
        levelWidths[level] = (levelWidths[level] || 0) + 1;
    });

    // Calcular posições reais
    const HORIZONTAL_SPACING = 250;
    const VERTICAL_SPACING = 150;

    // Contadores para cada nível
    const levelCounters = {};

    Object.entries(levels).forEach(([menuId, level]) => {
        levelCounters[level] = levelCounters[level] || 0;

        const width = levelWidths[level];
        const totalWidth = (width - 1) * HORIZONTAL_SPACING;
        const startX = -totalWidth / 2;

        const x = startX + levelCounters[level] * HORIZONTAL_SPACING;
        const y = level * VERTICAL_SPACING;

        positions[menuId] = { x, y };

        levelCounters[level]++;
    });

    return positions;
};

// Construir grafo de dependências
const buildDependencyGraph = (menus) => {
    const graph = {};

    Object.keys(menus).forEach((menuId) => {
        graph[menuId] = {
            inbound: [],
            outbound: [],
        };
    });

    Object.entries(menus).forEach(([menuId, menuData]) => {
        const options = menuData.options || {};

        // Verificar botões
        if (options.menu_type === 'button' && options.buttons) {
            options.buttons.forEach((button) => {
                if (button.next_menu && graph[button.next_menu]) {
                    graph[menuId].outbound.push(button.next_menu);
                    graph[button.next_menu].inbound.push(menuId);
                }
            });
        }

        // Verificar listas
        if (options.menu_type === 'list' && options.sections) {
            options.sections.forEach((section) => {
                if (section.rows) {
                    section.rows.forEach((row) => {
                        if (row.next_menu && graph[row.next_menu]) {
                            graph[menuId].outbound.push(row.next_menu);
                            graph[row.next_menu].inbound.push(menuId);
                        }
                    });
                }
            });
        }
    });

    return graph;
};

// Calcular níveis dos nós com base na distância aos nós raiz
const calculateNodeLevels = (graph, rootMenus) => {
    const levels = {};
    const visited = new Set();

    // Inicializar níveis para nós raiz
    rootMenus.forEach((menuId, index) => {
        levels[menuId] = index;
        visited.add(menuId);
    });

    // Função BFS para atribuir níveis
    const queue = [...rootMenus];

    while (queue.length > 0) {
        const current = queue.shift();
        const nextLevel = levels[current] + 1;

        graph[current].outbound.forEach((neighbor) => {
            if (!visited.has(neighbor)) {
                levels[neighbor] = nextLevel;
                visited.add(neighbor);
                queue.push(neighbor);
            }
        });
    }

    // Atribuir níveis para nós que não foram visitados (isolados)
    Object.keys(graph).forEach((menuId) => {
        if (!visited.has(menuId)) {
            levels[menuId] = Math.max(...Object.values(levels)) + 1;
        }
    });

    return levels;
};

// Função para gerar um ID de menu único
export const generateUniqueMenuId = (menus, baseName = 'menu') => {
    let counter = 1;
    let menuId = `${baseName}_${counter}`;

    while (menus[menuId]) {
        counter++;
        menuId = `${baseName}_${counter}`;
    }

    return menuId;
};

// Função para converter o fluxo visual do ReactFlow de volta para o formato JSON
export const convertFlowToData = (nodes, edges, originalFlowData) => {
    if (!originalFlowData || !originalFlowData.menus) {
        return { menus: {} };
    }

    const flowData = {
        ...originalFlowData,
        menus: { ...originalFlowData.menus },
    };

    // Atualizar os dados dos menus com base nos nós
    nodes.forEach((node) => {
        const { menuId, menuData } = node.data;

        if (menuId && menuData) {
            flowData.menus[menuId] = { ...menuData };
        }
    });

    // Atualizar as conexões com base nas arestas
    edges.forEach((edge) => {
        const { source, target } = edge;

        // Encontrar o menu de origem
        const sourceMenu = flowData.menus[source];
        if (!sourceMenu) return;

        // Verificar o tipo de menu e atualizar as conexões
        const options = sourceMenu.options || {};

        if (options.menu_type === 'button' && options.buttons) {
            // Procurar pelos botões que precisam ser atualizados
            options.buttons.forEach((button) => {
                // Se um botão está conectado a outro menu, atualizar a conexão
                if (edge.id.includes(`e-${source}-${button.next_menu}`)) {
                    button.next_menu = target;
                }
            });
        }

        if (options.menu_type === 'list' && options.sections) {
            options.sections.forEach((section) => {
                if (section.rows) {
                    section.rows.forEach((row) => {
                        // Se uma linha está conectada a outro menu, atualizar a conexão
                        if (edge.id.includes(`e-${source}-${row.next_menu}`)) {
                            row.next_menu = target;
                        }
                    });
                }
            });
        }
    });

    return flowData;
};

// Função para validar se um fluxo é válido
export const isFlowValid = (flowData) => {
    if (!flowData || !flowData.menus) {
        return { valid: false, error: 'Dados de fluxo inválidos' };
    }

    // Verificar menus obrigatórios
    if (!flowData.menus.privacidade) {
        return { valid: false, error: 'O menu "privacidade" é obrigatório' };
    }

    if (!flowData.menus.inicial) {
        return { valid: false, error: 'O menu "inicial" é obrigatório' };
    }

    // Verificar referências a menus inexistentes
    for (const [menuId, menuData] of Object.entries(flowData.menus)) {
        const options = menuData.options || {};

        if (options.menu_type === 'button' && options.buttons) {
            for (const button of options.buttons) {
                if (button.next_menu && !flowData.menus[button.next_menu]) {
                    return {
                        valid: false,
                        error: `No menu "${menuId}", o botão "${button.title}" aponta para um menu inexistente: "${button.next_menu}"`,
                    };
                }
            }
        }

        if (options.menu_type === 'list' && options.sections) {
            for (const section of options.sections) {
                if (section.rows) {
                    for (const row of section.rows) {
                        if (row.next_menu && !flowData.menus[row.next_menu]) {
                            return {
                                valid: false,
                                error: `No menu "${menuId}", o item "${row.title}" aponta para um menu inexistente: "${row.next_menu}"`,
                            };
                        }
                    }
                }
            }
        }
    }

    return { valid: true };
};
