/**
 * Documentation Viewer Page
 * Display specific documentation with table of contents
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Container,
  Button,
  Drawer,
  List,
  ListItem,
  ListItemText,
  IconButton,
  useMediaQuery,
  useTheme,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { docsAPI } from '../api';

export default function DocsViewer() {
  const { docId } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [doc, setDoc] = useState(null);
  const [toc, setToc] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tocOpen, setTocOpen] = useState(!isMobile);

  // Load document on mount or when docId changes
  useEffect(() => {
    if (docId) {
      loadDocument();
      loadTableOfContents();
    }
  }, [docId]);

  const loadDocument = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await docsAPI.getDocument(docId, 'html');
      setDoc(data);
    } catch (err) {
      console.error('Error loading document:', err);
      setError(err.response?.data?.detail || 'Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const loadTableOfContents = async () => {
    try {
      const data = await docsAPI.getTableOfContents(docId);
      setToc(data || []);
    } catch (err) {
      console.error('Error loading TOC:', err);
      // TOC is optional, don't show error
    }
  };

  // Scroll to anchor
  const scrollToAnchor = (anchor) => {
    const element = document.getElementById(anchor);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      if (isMobile) {
        setTocOpen(false);
      }
    }
  };

  // Go back to docs list
  const handleBack = () => {
    navigate('/docs');
  };

  // Toggle TOC drawer on mobile
  const toggleToc = () => {
    setTocOpen(!tocOpen);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !doc) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error || 'Document not found'}
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack}>
          Back to Documentation
        </Button>
      </Container>
    );
  }

  const mainHeaders = toc.filter((item) => item.level === 2);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Table of Contents Drawer */}
      {toc.length > 0 && (
        <Drawer
          variant={isMobile ? 'temporary' : 'permanent'}
          open={tocOpen}
          onClose={() => setTocOpen(false)}
          sx={{
            width: isMobile ? 250 : 280,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: isMobile ? 250 : 280,
              boxSizing: 'border-box',
              top: isMobile ? 0 : 64,
              height: isMobile ? '100%' : 'calc(100% - 64px)',
              borderRight: '1px solid',
              borderColor: 'divider',
            },
          }}
        >
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" fontWeight="bold">
              Contents
            </Typography>
            {isMobile && (
              <IconButton onClick={() => setTocOpen(false)} size="small">
                <CloseIcon />
              </IconButton>
            )}
          </Box>

          <List dense>
            {mainHeaders.map((item, index) => (
              <ListItem
                button
                key={index}
                onClick={() => scrollToAnchor(item.anchor)}
                sx={{
                  pl: item.level + 1,
                  '&:hover': { bgcolor: 'action.hover' },
                }}
              >
                <ListItemText
                  primary={item.title}
                  primaryTypographyProps={{
                    fontSize: '0.9rem',
                    fontWeight: item.level === 2 ? 'bold' : 'normal',
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Drawer>
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          ml: !isMobile && toc.length > 0 ? '280px' : 0,
        }}
      >
        <Container maxWidth="md">
          {/* Header */}
          <Box mb={3}>
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={handleBack}
              sx={{ mb: 2 }}
            >
              Back to Documentation
            </Button>

            {isMobile && toc.length > 0 && (
              <IconButton onClick={toggleToc} sx={{ ml: 2 }}>
                <MenuIcon />
              </IconButton>
            )}

            <Breadcrumbs sx={{ mb: 2 }}>
              <Link
                underline="hover"
                color="inherit"
                onClick={handleBack}
                sx={{ cursor: 'pointer' }}
              >
                Documentation
              </Link>
              <Typography color="text.primary">{doc.title}</Typography>
            </Breadcrumbs>

            <Typography variant="caption" color="text.secondary" display="block">
              {doc.category}
            </Typography>
          </Box>

          {/* Document Content */}
          <Paper elevation={2} sx={{ p: 4 }}>
            <Box
              className="markdown-content"
              dangerouslySetInnerHTML={{ __html: doc.content }}
              sx={{
                '& h1': { fontSize: '2rem', fontWeight: 'bold', mt: 3, mb: 2 },
                '& h2': { fontSize: '1.5rem', fontWeight: 'bold', mt: 3, mb: 1.5, color: 'primary.main' },
                '& h3': { fontSize: '1.25rem', fontWeight: 'bold', mt: 2, mb: 1 },
                '& h4': { fontSize: '1.1rem', fontWeight: 'bold', mt: 2, mb: 1 },
                '& p': { mb: 2, lineHeight: 1.7 },
                '& ul, & ol': { mb: 2, pl: 3 },
                '& li': { mb: 1 },
                '& code': {
                  bgcolor: 'grey.100',
                  p: 0.5,
                  borderRadius: 1,
                  fontSize: '0.9em',
                  fontFamily: 'monospace',
                },
                '& pre': {
                  bgcolor: 'grey.100',
                  p: 2,
                  borderRadius: 1,
                  overflow: 'auto',
                  '& code': { bgcolor: 'transparent', p: 0 },
                },
                '& table': {
                  width: '100%',
                  borderCollapse: 'collapse',
                  mb: 2,
                  '& th, & td': {
                    border: '1px solid',
                    borderColor: 'divider',
                    p: 1,
                    textAlign: 'left',
                  },
                  '& th': { bgcolor: 'grey.100', fontWeight: 'bold' },
                },
                '& blockquote': {
                  borderLeft: '4px solid',
                  borderColor: 'primary.main',
                  pl: 2,
                  ml: 0,
                  fontStyle: 'italic',
                  color: 'text.secondary',
                },
                '& img': { maxWidth: '100%', height: 'auto' },
              }}
            />
          </Paper>
        </Container>
      </Box>
    </Box>
  );
}
