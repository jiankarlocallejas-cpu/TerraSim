import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const DataUpload: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Data Upload
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>Data upload page - To be implemented with Leaflet and OpenLayers integration</Typography>
      </Paper>
    </Box>
  );
};

export default DataUpload;
