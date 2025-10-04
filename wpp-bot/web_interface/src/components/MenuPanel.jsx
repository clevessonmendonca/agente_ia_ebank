import React, { useState } from 'react';
import {
    Box,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Collapse,
    TextField,
    InputAdornment,
    Typography,
    Divider,
    Paper,
    IconButton,
    Tooltip,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import MessageIcon from '@mui/icons-material/Message';
import TouchAppIcon from '@mui/icons-material/TouchApp';
import FormatListBulletedIcon from '@mui/icons-material/FormatListBulleted';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';

// Menu types icons
const menuTypeIcons = {
    text: <MessageIcon fontSize="small" />,
    button: <TouchAppIcon fontSize="small" />,
    list: <FormatListBulletedIcon fontSize="small" />,
};

const MenuPanel = ({ flowData, onSelectMenu, onAddMenu, selectedMenuId }) => {
    const [expanded, setExpanded] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [categoryOpen, setCategoryOpen] = useState({
        system: true,
        info: true,
        user: true,
    });

    const handleCategoryToggle = (category) => {
        setCategoryOpen({
            ...categoryOpen,
            [category]: !categoryOpen[category],
        });
    };

    // Organizar menus por categorias
    const organizeMenusByCategory = () => {
        if (!flowData || !flowData.menus) return {};

        const categories = {
            system: [], // Menus do sistema (privacidade, inicial)
            info: [], // Menus informativos
            user: [], // Outros menus
        };

        Object.entries(flowData.menus).forEach(([menuId, menuData]) => {
            // Filtrar pela pesquisa
            if (
                searchTerm &&
                !menuId.toLowerCase().includes(searchTerm.toLowerCase()) &&
                !menuData.title
                    ?.toLowerCase()
                    .includes(searchTerm.toLowerCase())
            ) {
                return;
            }

            if (
                menuId === 'privacidade' ||
                menuId === 'inicial' ||
                menuId === 'encerrar_atendimento'
            ) {
                categories.system.push({ id: menuId, ...menuData });
            } else if (
                menuId.includes('info') ||
                menuId.includes('sobre') ||
                menuId.includes('missao')
            ) {
                categories.info.push({ id: menuId, ...menuData });
            } else {
                categories.user.push({ id: menuId, ...menuData });
            }
        });

        return categories;
    };

    const categorizedMenus = organizeMenusByCategory();

    return (
        <Paper
            sx={{
                width: expanded ? 250 : 'auto',
                height: '100%',
                borderRadius: 0,
                boxShadow: 2,
                display: 'flex',
                flexDirection: 'column',
                transition: 'width 0.3s ease',
            }}
        >
            <Box
                sx={{
                    p: 1,
                    display: 'flex',
                    alignItems: 'center',
                    borderBottom: '1px solid #e0e0e0',
                }}
            >
                <IconButton onClick={() => setExpanded(!expanded)} size="small">
                    {expanded ? <ExpandLess /> : <ExpandMore />}
                </IconButton>

                {expanded && (
                    <Typography variant="subtitle1" sx={{ flexGrow: 1, ml: 1 }}>
                        Menus
                    </Typography>
                )}

                {expanded && (
                    <Tooltip title="Adicionar Menu">
                        <IconButton size="small" onClick={() => onAddMenu()}>
                            <AddIcon fontSize="small" />
                        </IconButton>
                    </Tooltip>
                )}
            </Box>

            {expanded && (
                <Box sx={{ p: 1 }}>
                    <TextField
                        fullWidth
                        size="small"
                        placeholder="Buscar menu..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        InputProps={{
                            startAdornment: (
                                <InputAdornment position="start">
                                    <SearchIcon fontSize="small" />
                                </InputAdornment>
                            ),
                        }}
                    />
                </Box>
            )}

            <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                {expanded ? (
                    <>
                        {/* Categoria: Menus do Sistema */}
                        <ListItem
                            button
                            onClick={() => handleCategoryToggle('system')}
                        >
                            <ListItemIcon sx={{ minWidth: 36 }}>
                                <MenuIcon fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary="Menus do Sistema" />
                            {categoryOpen.system ? (
                                <ExpandLess />
                            ) : (
                                <ExpandMore />
                            )}
                        </ListItem>
                        <Collapse in={categoryOpen.system} timeout="auto">
                            <List dense component="div" disablePadding>
                                {categorizedMenus.system?.map((menu) => (
                                    <ListItem
                                        key={menu.id}
                                        button
                                        onClick={() => onSelectMenu(menu.id)}
                                        selected={selectedMenuId === menu.id}
                                        sx={{ pl: 4 }}
                                    >
                                        <ListItemIcon sx={{ minWidth: 36 }}>
                                            {
                                                menuTypeIcons[
                                                    menu.options?.menu_type ||
                                                        'text'
                                                ]
                                            }
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={menu.title || menu.id}
                                            primaryTypographyProps={{
                                                noWrap: true,
                                                variant: 'body2',
                                            }}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </Collapse>

                        <Divider />

                        {/* Categoria: Menus Informativos */}
                        <ListItem
                            button
                            onClick={() => handleCategoryToggle('info')}
                        >
                            <ListItemIcon sx={{ minWidth: 36 }}>
                                <MenuIcon fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary="Menus Informativos" />
                            {categoryOpen.info ? (
                                <ExpandLess />
                            ) : (
                                <ExpandMore />
                            )}
                        </ListItem>
                        <Collapse in={categoryOpen.info} timeout="auto">
                            <List dense component="div" disablePadding>
                                {categorizedMenus.info?.map((menu) => (
                                    <ListItem
                                        key={menu.id}
                                        button
                                        onClick={() => onSelectMenu(menu.id)}
                                        selected={selectedMenuId === menu.id}
                                        sx={{ pl: 4 }}
                                    >
                                        <ListItemIcon sx={{ minWidth: 36 }}>
                                            {
                                                menuTypeIcons[
                                                    menu.options?.menu_type ||
                                                        'text'
                                                ]
                                            }
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={menu.title || menu.id}
                                            primaryTypographyProps={{
                                                noWrap: true,
                                                variant: 'body2',
                                            }}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </Collapse>

                        <Divider />

                        {/* Categoria: Outros Menus */}
                        <ListItem
                            button
                            onClick={() => handleCategoryToggle('user')}
                        >
                            <ListItemIcon sx={{ minWidth: 36 }}>
                                <MenuIcon fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary="Outros Menus" />
                            {categoryOpen.user ? (
                                <ExpandLess />
                            ) : (
                                <ExpandMore />
                            )}
                        </ListItem>
                        <Collapse in={categoryOpen.user} timeout="auto">
                            <List dense component="div" disablePadding>
                                {categorizedMenus.user?.map((menu) => (
                                    <ListItem
                                        key={menu.id}
                                        button
                                        onClick={() => onSelectMenu(menu.id)}
                                        selected={selectedMenuId === menu.id}
                                        sx={{ pl: 4 }}
                                    >
                                        <ListItemIcon sx={{ minWidth: 36 }}>
                                            {
                                                menuTypeIcons[
                                                    menu.options?.menu_type ||
                                                        'text'
                                                ]
                                            }
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={menu.title || menu.id}
                                            primaryTypographyProps={{
                                                noWrap: true,
                                                variant: 'body2',
                                            }}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </Collapse>
                    </>
                ) : (
                    // Versão compacta quando o painel está recolhido
                    <List dense>
                        {Object.entries(flowData?.menus || {}).map(
                            ([menuId, menuData]) => (
                                <Tooltip
                                    key={menuId}
                                    title={menuData.title || menuId}
                                    placement="right"
                                >
                                    <ListItem
                                        button
                                        onClick={() => onSelectMenu(menuId)}
                                        selected={selectedMenuId === menuId}
                                    >
                                        <ListItemIcon sx={{ minWidth: 36 }}>
                                            {
                                                menuTypeIcons[
                                                    menuData.options
                                                        ?.menu_type || 'text'
                                                ]
                                            }
                                        </ListItemIcon>
                                    </ListItem>
                                </Tooltip>
                            )
                        )}
                    </List>
                )}
            </Box>
        </Paper>
    );
};

export default MenuPanel;
