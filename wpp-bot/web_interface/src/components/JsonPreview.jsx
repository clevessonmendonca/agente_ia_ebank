import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Paper,
    IconButton,
    Collapse,
    TextField,
} from '@mui/material';
import CodeIcon from '@mui/icons-material/Code';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

const JsonPreview = ({ data, title = 'JSON Preview' }) => {
    const [expanded, setExpanded] = useState(false);
    const [jsonString, setJsonString] = useState('');

    useEffect(() => {
        if (data) {
            try {
                setJsonString(JSON.stringify(data, null, 2));
            } catch (error) {
                console.error('Erro ao converter dados para JSON:', error);
                setJsonString('Erro ao gerar JSON');
            }
        } else {
            setJsonString('Nenhum dado disponível');
        }
    }, [data]);

    return (
        <Paper
            sx={{
                position: 'absolute',
                bottom: 0,
                right: 0,
                width: expanded ? 500 : 'auto',
                maxWidth: '100%',
                zIndex: 10,
                m: 2,
                boxShadow: 3,
            }}
        >
            <Box
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    p: 1,
                    backgroundColor: 'primary.main',
                    color: 'white',
                    borderTopLeftRadius: 4,
                    borderTopRightRadius: 4,
                }}
            >
                <CodeIcon sx={{ mr: 1 }} />
                <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
                    {title}
                </Typography>
                <IconButton
                    size="small"
                    onClick={() => setExpanded(!expanded)}
                    sx={{ color: 'white' }}
                >
                    {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
            </Box>

            <Collapse in={expanded}>
                <Box sx={{ p: 1 }}>
                    <TextField
                        fullWidth
                        multiline
                        rows={15}
                        value={jsonString}
                        variant="outlined"
                        size="small"
                        InputProps={{
                            readOnly: true,
                            sx: {
                                fontFamily: 'monospace',
                                fontSize: '0.8rem',
                            },
                        }}
                    />
                </Box>
            </Collapse>
        </Paper>
    );
};

export default JsonPreview;
