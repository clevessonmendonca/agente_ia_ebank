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
import { v4 as uuidv4 } from 'uuid';

const ButtonsEditor = ({ buttons = [], onChange }) => {
    const [open, setOpen] = useState(false);
    const [currentButton, setCurrentButton] = useState(null);
    const [editMode, setEditMode] = useState(false);

    const handleOpen = () => {
        setCurrentButton({ id: uuidv4(), title: '', next_menu: '' });
        setEditMode(false);
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
        setCurrentButton(null);
    };

    const handleEdit = (button, index) => {
        setCurrentButton({ ...button, index });
        setEditMode(true);
        setOpen(true);
    };

    const handleDelete = (index) => {
        const updatedButtons = [...buttons];
        updatedButtons.splice(index, 1);
        onChange(updatedButtons);
    };

    const handleSave = () => {
        if (!currentButton.title) {
            return; // Não salvar se o título estiver vazio
        }

        const updatedButtons = [...buttons];

        if (editMode && currentButton.index !== undefined) {
            // Editar botão existente
            const { index, ...buttonData } = currentButton;
            updatedButtons[index] = buttonData;
        } else {
            // Adicionar novo botão
            const { index, ...buttonData } = currentButton;
            updatedButtons.push(buttonData);
        }

        onChange(updatedButtons);
        handleClose();
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
                <Typography variant="subtitle1">Botões</Typography>
                <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    size="small"
                    onClick={handleOpen}
                >
                    Adicionar Botão
                </Button>
            </Box>

            {buttons.length === 0 ? (
                <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ textAlign: 'center', py: 2 }}
                >
                    Nenhum botão cadastrado
                </Typography>
            ) : (
                <List>
                    {buttons.map((button, index) => (
                        <ListItem
                            key={button.id || index}
                            secondaryAction={
                                <Box>
                                    <IconButton
                                        edge="end"
                                        onClick={() =>
                                            handleEdit(button, index)
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
                                primary={button.title}
                                secondary={
                                    <>
                                        <Typography
                                            variant="caption"
                                            component="span"
                                            display="block"
                                            color="text.secondary"
                                        >
                                            ID: {button.id}
                                        </Typography>
                                        <Typography
                                            variant="caption"
                                            component="span"
                                            display="block"
                                            color="text.secondary"
                                        >
                                            Próximo Menu:{' '}
                                            {button.next_menu || 'Nenhum'}
                                        </Typography>
                                        {button.action && (
                                            <Typography
                                                variant="caption"
                                                component="span"
                                                display="block"
                                                color="text.secondary"
                                            >
                                                Ação: {button.action}
                                            </Typography>
                                        )}
                                    </>
                                }
                            />
                        </ListItem>
                    ))}
                </List>
            )}

            <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
                <DialogTitle>
                    {editMode ? 'Editar Botão' : 'Novo Botão'}
                </DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="ID"
                        fullWidth
                        value={currentButton?.id || ''}
                        onChange={(e) =>
                            setCurrentButton({
                                ...currentButton,
                                id: e.target.value,
                            })
                        }
                        helperText="Identificador único do botão"
                    />
                    <TextField
                        margin="dense"
                        label="Título"
                        fullWidth
                        value={currentButton?.title || ''}
                        onChange={(e) =>
                            setCurrentButton({
                                ...currentButton,
                                title: e.target.value,
                            })
                        }
                        helperText="Texto exibido no botão"
                    />
                    <TextField
                        margin="dense"
                        label="Próximo Menu"
                        fullWidth
                        value={currentButton?.next_menu || ''}
                        onChange={(e) =>
                            setCurrentButton({
                                ...currentButton,
                                next_menu: e.target.value,
                            })
                        }
                        helperText="ID do menu que será exibido após clicar no botão"
                    />
                    <TextField
                        margin="dense"
                        label="Ação"
                        fullWidth
                        value={currentButton?.action || ''}
                        onChange={(e) =>
                            setCurrentButton({
                                ...currentButton,
                                action: e.target.value,
                            })
                        }
                        helperText="Ação especial a ser executada (opcional)"
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleClose}>Cancelar</Button>
                    <Button onClick={handleSave}>Salvar</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ButtonsEditor;
