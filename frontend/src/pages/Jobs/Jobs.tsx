import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const Jobs: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Jobs
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>Background jobs management page - To be implemented</Typography>
      </Paper>
    </Box>
  );
};

export default Jobs;
