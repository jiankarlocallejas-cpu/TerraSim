import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const JobDetail: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Job Details
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>Job detail page - To be implemented</Typography>
      </Paper>
    </Box>
  );
};

export default JobDetail;
