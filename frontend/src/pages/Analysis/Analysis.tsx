import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const Analysis: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Analysis
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>Erosion analysis page - To be implemented with mapping components</Typography>
      </Paper>
    </Box>
  );
};

export default Analysis;
