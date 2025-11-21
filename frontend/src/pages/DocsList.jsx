/**
 * ============================================================================
 * Documentation List Page
 * ============================================================================
 * Version: 1.1.0
 * Created: 2025-11-20
 * Last Updated: 2025-11-21
 *
 * Description:
 *   Browse all available documentation organized by categories. Includes
 *   real-time search functionality across all docs.
 *
 * Features:
 *   - Display docs organized by category (General, Modules)
 *   - Real-time search with debouncing
 *   - Click any doc to navigate to viewer
 *   - Search results with context highlighting
 *   - Mobile responsive cards
 *   - Loading and error states
 *
 * Changelog:
 * ----------
 * v1.1.0 (2025-11-21):
 *   - Converted Material-UI icon imports to individual imports for better tree-shaking
 *   - Migrated from react-query v3 to @tanstack/react-query v5
 *   - Bundle size optimization as part of code splitting initiative
 *
 * v1.0.0 (2025-11-20):
 *   - Initial implementation
 *   - Category-based organization
 *   - Search across all documentation
 *   - Material-UI components
 *   - Responsive design
 * ============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActionArea,
  Grid,
  TextField,
  InputAdornment,
  Chip,
  CircularProgress,
  Alert,
  Container,
  Paper,
  Divider,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ArticleIcon from '@mui/icons-material/Article';
import SchoolIcon from '@mui/icons-material/School';
import InfoIcon from '@mui/icons-material/Info';
import { docsAPI } from '../api';

export default function DocsList() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);

  // Load categories on mount
  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await docsAPI.getCategories();
      setCategories(data.categories || []);
    } catch (err) {
      console.error('Error loading documentation:', err);
      setError(err.response?.data?.detail || 'Failed to load documentation');
    } finally {
      setLoading(false);
    }
  };

  // Handle search
  const handleSearch = async (query) => {
    setSearchQuery(query);

    if (!query || query.trim().length < 2) {
      setSearchResults(null);
      return;
    }

    try {
      setSearching(true);
      const data = await docsAPI.searchDocs(query.trim(), 20);
      setSearchResults(data);
    } catch (err) {
      console.error('Error searching documentation:', err);
      setError(err.response?.data?.detail || 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  // Navigate to specific doc
  const handleDocClick = (docId) => {
    navigate(`/docs/${docId}`);
  };

  // Navigate to doc from search result
  const handleSearchResultClick = (docId) => {
    setSearchQuery('');
    setSearchResults(null);
    navigate(`/docs/${docId}`);
  };

  // Get icon for category
  const getCategoryIcon = (categoryName) => {
    switch (categoryName.toLowerCase()) {
      case 'general':
        return <InfoIcon />;
      case 'modules':
        return <SchoolIcon />;
      default:
        return <ArticleIcon />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" gutterBottom fontWeight="bold">
          📚 Help & Documentation
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Learn how to use the Farm Management System with easy-to-follow guides
        </Typography>
      </Box>

      {/* Search Bar */}
      <Paper elevation={2} sx={{ p: 2, mb: 4 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search documentation... (e.g., 'feeding', 'inventory', 'users')"
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                {searching ? <CircularProgress size={20} /> : <SearchIcon />}
              </InputAdornment>
            ),
          }}
        />
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Search Results */}
      {searchResults && searchResults.total_results > 0 && (
        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            🔍 Search Results ({searchResults.total_results} found)
          </Typography>
          <Divider sx={{ my: 2 }} />
          <Box>
            {searchResults.results.map((result, index) => (
              <Card
                key={index}
                variant="outlined"
                sx={{ mb: 2, cursor: 'pointer' }}
                onClick={() => handleSearchResultClick(result.doc_id)}
              >
                <CardContent>
                  <Typography variant="subtitle1" fontWeight="bold" color="primary">
                    {result.doc_title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Line {result.line_number}
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    ...{result.match.substring(0, 200)}...
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Box>
        </Paper>
      )}

      {/* No Search Results */}
      {searchResults && searchResults.total_results === 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          No results found for "{searchQuery}". Try different keywords.
        </Alert>
      )}

      {/* Documentation Categories */}
      {!searchResults && categories.map((category) => (
        <Box key={category.name} mb={4}>
          <Box display="flex" alignItems="center" mb={2}>
            {getCategoryIcon(category.name)}
            <Typography variant="h5" fontWeight="bold" ml={1}>
              {category.name}
            </Typography>
          </Box>

          <Grid container spacing={3}>
            {category.docs.map((doc) => (
              <Grid item xs={12} sm={6} md={4} key={doc.id}>
                <Card elevation={3} sx={{ height: '100%' }}>
                  <CardActionArea
                    onClick={() => handleDocClick(doc.id)}
                    sx={{ height: '100%', p: 2 }}
                  >
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {doc.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {doc.description}
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      ))}

      {/* Empty State */}
      {!searchResults && categories.length === 0 && (
        <Alert severity="info">
          No documentation available at this time.
        </Alert>
      )}
    </Container>
  );
}
