import React, { useState } from 'react';
import {
    Box,
    Typography,
    Button,
    TextField,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    List,
    ListItem,
    ListItemText,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { v4 as uuidv4 } from 'uuid';

const ListEditor = ({ listOptions = {}, onChange }) => {
    const [sectionDialogOpen, setSectionDialogOpen] = useState(false);
    const [rowDialogOpen, setRowDialogOpen] = useState(false);
    const [currentSection, setCurrentSection] = useState(null);
    const [currentRow, setCurrentRow] = useState(null);
    const [editMode, setEditMode] = useState(false);
    const [selectedSectionIndex, setSelectedSectionIndex] = useState(null);

    const sections = listOptions.sections || [];

    const handleOpenSectionDialog = () => {
        setCurrentSection({ title: '' });
        setEditMode(false);
        setSectionDialogOpen(true);
    };

    const handleCloseSectionDialog = () => {
        setSectionDialogOpen(false);
        setCurrentSection(null);
    };

    const handleEditSection = (section, index) => {
        setCurrentSection({ ...section, index });
        setEditMode(true);
        setSectionDialogOpen(true);
    };

    const handleDeleteSection = (index) => {
        const updatedSections = [...sections];
        updatedSections.splice(index, 1);

        const updatedOptions = {
            ...listOptions,
            sections: updatedSections,
        };

        onChange(updatedOptions);
    };

    const handleSaveSection = () => {
        if (!currentSection.title) {
            return; // Não salvar se o título estiver vazio
        }

        const updatedSections = [...sections];

        if (editMode && currentSection.index !== undefined) {
            // Editar seção existente
            const { index, ...sectionData } = currentSection;
            updatedSections[index] = {
                ...updatedSections[index],
                title: sectionData.title,
            };
        } else {
            // Adicionar nova seção
            updatedSections.push({
                title: currentSection.title,
                rows: [],
            });
        }

        const updatedOptions = {
            ...listOptions,
            sections: updatedSections,
        };

        onChange(updatedOptions);
        handleCloseSectionDialog();
    };

    const handleOpenRowDialog = (sectionIndex) => {
        setSelectedSectionIndex(sectionIndex);
        setCurrentRow({ id: uuidv4(), title: '', description: '' });
        setEditMode(false);
        setRowDialogOpen(true);
    };

    const handleCloseRowDialog = () => {
        setRowDialogOpen(false);
        setCurrentRow(null);
    };

    const handleEditRow = (row, rowIndex, sectionIndex) => {
        setSelectedSectionIndex(sectionIndex);
        setCurrentRow({ ...row, index: rowIndex });
        setEditMode(true);
        setRowDialogOpen(true);
    };

    const handleDeleteRow = (rowIndex, sectionIndex) => {
        const updatedSections = [...sections];
        updatedSections[sectionIndex].rows.splice(rowIndex, 1);

        const updatedOptions = {
            ...listOptions,
            sections: updatedSections,
        };

        onChange(updatedOptions);
    };

    const handleSaveRow = () => {
        if (!currentRow.title) {
            return; // Não salvar se o título estiver vazio
        }

        const updatedSections = [...sections];
        const currentSectionRows =
            updatedSections[selectedSectionIndex].rows || [];

        if (editMode && currentRow.index !== undefined) {
            // Editar linha existente
            const { index, ...rowData } = currentRow;
            currentSectionRows[index] = rowData;
        } else {
            // Adicionar nova linha
            const { index, ...rowData } = currentRow;
            currentSectionRows.push(rowData);
        }

        updatedSections[selectedSectionIndex].rows = currentSectionRows;

        const updatedOptions = {
            ...listOptions,
            sections: updatedSections,
        };

        onChange(updatedOptions);
        handleCloseRowDialog();
    };

    return (
        <Box>
            <TextField
                label="Cabeçalho"
                fullWidth
                margin="normal"
                value={listOptions.header || ''}
                onChange={(e) =>
                    onChange({
                        ...listOptions,
                        header: e.target.value,
                    })
                }
            />

            <TextField
                label="Texto do Botão"
                fullWidth
                margin="normal"
                value={listOptions.button_text || ''}
                onChange={(e) =>
                    onChange({
                        ...listOptions,
                        button_text: e.target.value,
                    })
                }
            />

            <TextField
                label="Rodapé"
                fullWidth
                margin="normal"
                value={listOptions.footer || ''}
                onChange={(e) =>
                    onChange({
                        ...listOptions,
                        footer: e.target.value,
                    })
                }
            />

            <Divider sx={{ my: 2 }} />

            <Box
                sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 2,
                }}
            >
                <Typography variant="subtitle1">Seções</Typography>
                <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    size="small"
                    onClick={handleOpenSectionDialog}
                >
                    Adicionar Seção
                </Button>
            </Box>

            {sections.length === 0 ? (
                <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ textAlign: 'center', py: 2 }}
                >
                    Nenhuma seção cadastrada
                </Typography>
            ) : (
                sections.map((section, sectionIndex) => (
                    <Accordion key={sectionIndex}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Box
                                sx={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    width: '100%',
                                    alignItems: 'center',
                                }}
                            >
                                <Typography>{section.title}</Typography>
                                <Box onClick={(e) => e.stopPropagation()}>
                                    <IconButton
                                        size="small"
                                        onClick={() =>
                                            handleEditSection(
                                                section,
                                                sectionIndex
                                            )
                                        }
                                    >
                                        <EditIcon fontSize="small" />
                                    </IconButton>
                                    <IconButton
                                        size="small"
                                        onClick={() =>
                                            handleDeleteSection(sectionIndex)
                                        }
                                    >
                                        <DeleteIcon fontSize="small" />
                                    </IconButton>
                                </Box>
                            </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                            <Box
                                sx={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    mb: 2,
                                }}
                            >
                                <Typography variant="subtitle2">
                                    Itens
                                </Typography>
                                <Button
                                    variant="outlined"
                                    startIcon={<AddIcon />}
                                    size="small"
                                    onClick={() =>
                                        handleOpenRowDialog(sectionIndex)
                                    }
                                >
                                    Adicionar Item
                                </Button>
                            </Box>

                            {!section.rows || section.rows.length === 0 ? (
                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                    sx={{ textAlign: 'center', py: 2 }}
                                >
                                    Nenhum item cadastrado
                                </Typography>
                            ) : (
                                <List dense>
                                    {section.rows.map((row, rowIndex) => (
                                        <ListItem
                                            key={row.id || rowIndex}
                                            secondaryAction={
                                                <Box>
                                                    <IconButton
                                                        edge="end"
                                                        onClick={() =>
                                                            handleEditRow(
                                                                row,
                                                                rowIndex,
                                                                sectionIndex
                                                            )
                                                        }
                                                    >
                                                        <EditIcon fontSize="small" />
                                                    </IconButton>
                                                    <IconButton
                                                        edge="end"
                                                        onClick={() =>
                                                            handleDeleteRow(
                                                                rowIndex,
                                                                sectionIndex
                                                            )
                                                        }
                                                    >
                                                        <DeleteIcon fontSize="small" />
                                                    </IconButton>
                                                </Box>
                                            }
                                        >
                                            <ListItemText
                                                primary={row.title}
                                                secondary={
                                                    <>
                                                        <Typography
                                                            variant="caption"
                                                            component="span"
                                                            display="block"
                                                            color="text.secondary"
                                                        >
                                                            ID: {row.id}
                                                        </Typography>
                                                        {row.description && (
                                                            <Typography
                                                                variant="caption"
                                                                component="span"
                                                                display="block"
                                                                color="text.secondary"
                                                            >
                                                                Descrição:{' '}
                                                                {
                                                                    row.description
                                                                }
                                                            </Typography>
                                                        )}
                                                    </>
                                                }
                                            />
                                        </ListItem>
                                    ))}
                                </List>
                            )}
                        </AccordionDetails>
                    </Accordion>
                ))
            )}

            {/* Dialog para adicionar/editar seção */}
            <Dialog
                open={sectionDialogOpen}
                onClose={handleCloseSectionDialog}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>
                    {editMode ? 'Editar Seção' : 'Nova Seção'}
                </DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Título"
                        fullWidth
                        value={currentSection?.title || ''}
                        onChange={(e) =>
                            setCurrentSection({
                                ...currentSection,
                                title: e.target.value,
                            })
                        }
                        helperText="Título da seção"
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseSectionDialog}>Cancelar</Button>
                    <Button onClick={handleSaveSection}>Salvar</Button>
                </DialogActions>
            </Dialog>

            {/* Dialog para adicionar/editar item */}
            <Dialog
                open={rowDialogOpen}
                onClose={handleCloseRowDialog}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>
                    {editMode ? 'Editar Item' : 'Novo Item'}
                </DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="ID"
                        fullWidth
                        value={currentRow?.id || ''}
                        onChange={(e) =>
                            setCurrentRow({ ...currentRow, id: e.target.value })
                        }
                        helperText="Identificador único do item"
                    />
                    <TextField
                        margin="dense"
                        label="Título"
                        fullWidth
                        value={currentRow?.title || ''}
                        onChange={(e) =>
                            setCurrentRow({
                                ...currentRow,
                                title: e.target.value,
                            })
                        }
                        helperText="Texto principal do item"
                    />
                    <TextField
                        margin="dense"
                        label="Descrição"
                        fullWidth
                        value={currentRow?.description || ''}
                        onChange={(e) =>
                            setCurrentRow({
                                ...currentRow,
                                description: e.target.value,
                            })
                        }
                        helperText="Descrição adicional (opcional)"
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseRowDialog}>Cancelar</Button>
                    <Button onClick={handleSaveRow}>Salvar</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ListEditor;
