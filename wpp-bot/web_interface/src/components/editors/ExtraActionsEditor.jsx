import React, { useState } from 'react';
import {
    Box,
    Typography,
    Button,
    TextField,
    List,
    ListItem,
    ListItemText,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

const ExtraActionsEditor = ({ extraActions = [], onChange }) => {
    const [open, setOpen] = useState(false);
    const [currentAction, setCurrentAction] = useState(null);
    const [editMode, setEditMode] = useState(false);

    const handleOpen = () => {
        setCurrentAction({ type: 'message', content: '' });
        setEditMode(false);
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
        setCurrentAction(null);
    };

    const handleEdit = (action, index) => {
        setCurrentAction({ ...action, index });
        setEditMode(true);
        setOpen(true);
    };

    const handleDelete = (index) => {
        const updatedActions = [...extraActions];
        updatedActions.splice(index, 1);
        onChange(updatedActions);
    };

    const handleSave = () => {
        if (!currentAction.type) {
            return; // Não salvar se o tipo estiver vazio
        }

        const updatedActions = [...extraActions];

        if (editMode && currentAction.index !== undefined) {
            // Editar ação existente
            const { index, ...actionData } = currentAction;
            updatedActions[index] = actionData;
        } else {
            // Adicionar nova ação
            const { index, ...actionData } = currentAction;
            updatedActions.push(actionData);
        }

        onChange(updatedActions);
        handleClose();
    };

    const renderActionFields = () => {
        if (!currentAction) return null;

        const fields = [];

        // Campos comuns para todos os tipos
        fields.push(
            <FormControl key="type-field" fullWidth margin="dense">
                <InputLabel>Tipo de Ação</InputLabel>
                <Select
                    value={currentAction.type || ''}
                    label="Tipo de Ação"
                    onChange={(e) =>
                        setCurrentAction({
                            ...currentAction,
                            type: e.target.value,
                        })
                    }
                >
                    <MenuItem value="message">Mensagem</MenuItem>
                    <MenuItem value="contact">Contato</MenuItem>
                    <MenuItem value="location">Localização</MenuItem>
                    <MenuItem value="link">Link</MenuItem>
                </Select>
            </FormControl>
        );

        // Campos específicos para cada tipo
        switch (currentAction.type) {
            case 'message':
                fields.push(
                    <TextField
                        key="content-field"
                        margin="dense"
                        label="Conteúdo"
                        fullWidth
                        multiline
                        rows={3}
                        value={currentAction.content || ''}
                        onChange={(e) =>
                            setCurrentAction({
                                ...currentAction,
                                content: e.target.value,
                            })
                        }
                    />
                );
                break;

            case 'contact':
                fields.push(
                    <TextField
                        key="name-field"
                        margin="dense"
                        label="Nome"
                        fullWidth
                        value={currentAction.name || ''}
                        onChange={(e) =>
                            setCurrentAction({
                                ...currentAction,
                                name: e.target.value,
                            })
                        }
                    />
                );
                fields.push(
                    <TextField
                        key="phone-field"
                        margin="dense"
                        label="Telefone"
                        fullWidth
                        value={currentAction.phone || ''}
                        onChange={(e) =>
                            setCurrentAction({
                                ...currentAction,
                                phone: e.target.value,
                            })
                        }
                    />
                );
                break;

            case 'location':
                fields.push(
                    <TextField
                        key="name-field"
                        margin="dense"
                        label="Nome"
                        fullWidth
                        value={currentAction.name || ''}
                        onChange={(e) =>
                            setCurrentAction({
                                ...currentAction,
                                name: e.target.value,
                            })
                        }
                    />
                );
                fields.push(
                    <TextField
                        key="address-field"
                        margin="dense"
                        label="Endereço"
                        fullWidth
                        value={currentAction.address || ''}
                        onChange={(e) =>
                            setCurrentAction({
                                ...currentAction,
                                address: e.target.value,
                            })
                        }
                    />
                );
                fields.push(
                    <TextField
                        key="latitude-field"
                        margin="dense"
                        label="Latitude"
                        fullWidth
                        value={currentAction.latitude || ''}
                        onChange={(e) =>
                            setCurrentAction({
                                ...currentAction,
                                latitude: e.target.value,
                            })
                        }
                    />
                );
                fields.push(
                    <TextField
                        key="longitude-field"
                        margin="dense"
                        label="Longitude"
                        fullWidth
                        value={currentAction.longitude || ''}
                        onChange={(e) =>
                            setCurrentAction({
                                ...currentAction,
                                longitude: e.target.value,
                            })
                        }
                    />
                );
                break;

            case 'link':
                fields.push(
                    <TextField
                        key="title-field"
                        margin="dense"
                        label="Título"
                        fullWidth
                        value={currentAction.title || ''}
                        onChange={(e) =>
                            setCurrentAction({
                                ...currentAction,
                                title: e.target.value,
                            })
                        }
                    />
                );
                fields.push(
                    <TextField
                        key="message-field"
                        margin="dense"
                        label="Mensagem"
                        fullWidth
                        multiline
                        rows={2}
                        value={currentAction.message || ''}
                        onChange={(e) =>
                            setCurrentAction({
                                ...currentAction,
                                message: e.target.value,
                            })
                        }
                    />
                );
                fields.push(
                    <TextField
                        key="url-field"
                        margin="dense"
                        label="URL"
                        fullWidth
                        value={currentAction.url || ''}
                        onChange={(e) =>
                            setCurrentAction({
                                ...currentAction,
                                url: e.target.value,
                            })
                        }
                    />
                );
                fields.push(
                    <TextField
                        key="button_text-field"
                        margin="dense"
                        label="Texto do Botão"
                        fullWidth
                        value={currentAction.button_text || ''}
                        onChange={(e) =>
                            setCurrentAction({
                                ...currentAction,
                                button_text: e.target.value,
                            })
                        }
                    />
                );
                break;

            default:
                break;
        }

        return fields;
    };

    return (
        <Box>
            <Box
                sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 2,
                }}
            >
                <Typography variant="subtitle1">Ações Extras</Typography>
                <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    size="small"
                    onClick={handleOpen}
                >
                    Adicionar Ação
                </Button>
            </Box>

            {extraActions.length === 0 ? (
                <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ textAlign: 'center', py: 2 }}
                >
                    Nenhuma ação extra cadastrada
                </Typography>
            ) : (
                <List>
                    {extraActions.map((action, index) => (
                        <ListItem
                            key={index}
                            secondaryAction={
                                <Box>
                                    <IconButton
                                        edge="end"
                                        onClick={() =>
                                            handleEdit(action, index)
                                        }
                                    >
                                        <EditIcon fontSize="small" />
                                    </IconButton>
                                    <IconButton
                                        edge="end"
                                        onClick={() => handleDelete(index)}
                                    >
                                        <DeleteIcon fontSize="small" />
                                    </IconButton>
                                </Box>
                            }
                        >
                            <ListItemText
                                primary={`${
                                    action.type.charAt(0).toUpperCase() +
                                    action.type.slice(1)
                                }`}
                                secondary={renderActionDetails(action)}
                            />
                        </ListItem>
                    ))}
                </List>
            )}

            <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
                <DialogTitle>
                    {editMode ? 'Editar Ação Extra' : 'Nova Ação Extra'}
                </DialogTitle>
                <DialogContent>{renderActionFields()}</DialogContent>
                <DialogActions>
                    <Button onClick={handleClose}>Cancelar</Button>
                    <Button onClick={handleSave}>Salvar</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

// Função para renderizar detalhes da ação na lista
const renderActionDetails = (action) => {
    switch (action.type) {
        case 'message':
            return (
                <Typography
                    variant="caption"
                    component="span"
                    display="block"
                    color="text.secondary"
                >
                    {action.content
                        ? `"${action.content.substring(0, 30)}${
                              action.content.length > 30 ? '...' : ''
                          }"`
                        : 'Sem conteúdo'}
                </Typography>
            );

        case 'contact':
            return (
                <>
                    <Typography
                        variant="caption"
                        component="span"
                        display="block"
                        color="text.secondary"
                    >
                        Nome: {action.name || 'Não definido'}
                    </Typography>
                    <Typography
                        variant="caption"
                        component="span"
                        display="block"
                        color="text.secondary"
                    >
                        Telefone: {action.phone || 'Não definido'}
                    </Typography>
                </>
            );

        case 'location':
            return (
                <>
                    <Typography
                        variant="caption"
                        component="span"
                        display="block"
                        color="text.secondary"
                    >
                        Local: {action.name || 'Não definido'}
                    </Typography>
                    <Typography
                        variant="caption"
                        component="span"
                        display="block"
                        color="text.secondary"
                    >
                        {action.latitude}, {action.longitude}
                    </Typography>
                </>
            );

        case 'link':
            return (
                <>
                    <Typography
                        variant="caption"
                        component="span"
                        display="block"
                        color="text.secondary"
                    >
                        Título: {action.title || 'Não definido'}
                    </Typography>
                    <Typography
                        variant="caption"
                        component="span"
                        display="block"
                        color="text.secondary"
                    >
                        URL: {action.url || 'Não definido'}
                    </Typography>
                </>
            );

        default:
            return null;
    }
};

export default ExtraActionsEditor;
