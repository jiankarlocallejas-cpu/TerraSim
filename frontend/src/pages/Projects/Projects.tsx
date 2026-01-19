import React from 'react';
import { Box, Typography, Button, Grid, Card, CardContent } from '@mui/material';
import { Add as AddIcon, Folder as FolderIcon } from '@mui/icons-material';

const Projects: React.FC = () => {
  // Mock data
  const projects = [
    { id: 1, name: 'Coastal Erosion Study', description: 'Analysis of coastal erosion patterns', status: 'Active' },
    { id: 2, name: 'River Basin Analysis', description: 'Sediment transport modeling', status: 'Completed' },
    { id: 3, name: 'Urban Development Impact', description: 'Urbanization effects on erosion', status: 'In Progress' },
  ];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Projects</Typography>
        <Button variant="contained" startIcon={<AddIcon />}>
          New Project
        </Button>
      </Box>

      <Grid container spacing={3}>
        {projects.map((project) => (
          <Grid item xs={12} sm={6} md={4} key={project.id}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <FolderIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">{project.name}</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  {project.description}
                </Typography>
                <Typography variant="caption" color="primary">
                  {project.status}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default Projects;
