import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';

const MenuNode = ({ data, isConnectable }) => {
    const { menuId, menuData } = data;
    const menuType = menuData.options?.menu_type || 'text';

    // Cores para diferentes tipos de menus
    const menuTypeColors = {
        text: '#e3f2fd', // Azul claro
        button: '#e8f5e9', // Verde claro
        list: '#fff8e1', // Amarelo claro
    };

    return (
        <Card
            variant="outlined"
            sx={{
                width: 200,
                backgroundColor: menuTypeColors[menuType] || '#ffffff',
            }}
        >
            <CardContent sx={{ p: 1 }}>
                <Handle
                    type="target"
                    position={Position.Top}
                    isConnectable={isConnectable}
                />

                <Box sx={{ mb: 1 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                        {menuData.title || 'Sem título'}
                    </Typography>
                    <Chip
                        label={menuType}
                        size="small"
                        sx={{ fontSize: '0.7rem' }}
                    />
                </Box>

                <Typography
                    variant="body2"
                    sx={{
                        mb: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                    }}
                >
                    {menuData.content || 'Sem conteúdo'}
                </Typography>

                {menuType === 'button' && menuData.options?.buttons && (
                    <Box>
                        <Typography variant="caption" sx={{ display: 'block' }}>
                            Botões: {menuData.options.buttons.length}
                        </Typography>
                    </Box>
                )}

                {menuType === 'list' && menuData.options?.sections && (
                    <Box>
                        <Typography variant="caption" sx={{ display: 'block' }}>
                            Seções: {menuData.options.sections.length}
                        </Typography>
                    </Box>
                )}

                <Handle
                    type="source"
                    position={Position.Bottom}
                    isConnectable={isConnectable}
                />
            </CardContent>
        </Card>
    );
};

export default memo(MenuNode);
