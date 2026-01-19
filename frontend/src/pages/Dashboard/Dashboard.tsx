import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
} from '@mui/material';
import {
  Folder as FolderIcon,
  CloudUpload as CloudUploadIcon,
  Analytics as AnalyticsIcon,
  Work as WorkIcon,
} from '@mui/icons-material';

const Dashboard: React.FC = () => {
  // Mock data - in real app, this would come from API
  const stats = {
    projects: 12,
    datasets: 48,
    analyses: 23,
    jobs: 7,
  };

  const recentActivity = [
    { id: 1, type: 'analysis', description: 'Erosion analysis completed for Project Alpha', time: '2 hours ago' },
    { id: 2, type: 'upload', description: 'Point cloud data uploaded to Project Beta', time: '4 hours ago' },
    { id: 3, type: 'job', description: 'Model training started for erosion prediction', time: '6 hours ago' },
    { id: 4, type: 'project', description: 'New project "Coastal Study" created', time: '1 day ago' },
  ];

  const StatCard: React.FC<{ title: string; value: number; icon: React.ReactNode; color: string }> = ({
    title,
    value,
    icon,
    color,
  }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <Box sx={{ color, mr: 2 }}>{icon}</Box>
          <Typography variant="h6" component="div">
            {title}
          </Typography>
        </Box>
        <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Welcome to TerraSim! Here's an overview of your GIS erosion modeling activities.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Projects"
            value={stats.projects}
            icon={<FolderIcon />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Datasets"
            value={stats.datasets}
            icon={<CloudUploadIcon />}
            color="#388e3c"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Analyses"
            value={stats.analyses}
            icon={<AnalyticsIcon />}
            color="#f57c00"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Jobs"
            value={stats.jobs}
            icon={<WorkIcon />}
            color="#d32f2f"
          />
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <List>
              {recentActivity.map((activity) => (
                <ListItem key={activity.id} divider>
                  <ListItemText
                    primary={activity.description}
                    secondary={activity.time}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              System Status
            </Typography>
            <Box mb={2}>
              <Typography variant="body2" gutterBottom>
                Processing Queue
              </Typography>
              <LinearProgress variant="determinate" value={30} />
            </Box>
            <Box mb={2}>
              <Typography variant="body2" gutterBottom>
                Storage Usage
              </Typography>
              <LinearProgress variant="determinate" value={65} color="warning" />
            </Box>
            <Box>
              <Typography variant="body2" gutterBottom>
                API Response Time
              </Typography>
              <LinearProgress variant="determinate" value={85} color="success" />
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
