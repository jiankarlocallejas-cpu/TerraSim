import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { createTheme, ThemeProvider, CssBaseline } from '@mui/material/styles';

// Debug log to confirm the file is being loaded
console.log('functional-app.tsx is loading...');

// Type definitions
interface ErosionInput {
  rainfall: number;
  slope: number;
  slope_length: number;
  soil_type: string;
  vegetation_cover: number;
  support_practices: number;
  land_use: string;
  area: number;
  seasonality: string;
}

interface ErosionResult {
  mean_loss: number;
  peak_loss: number;
  total_soil_loss: number;
  confidence: number;
  risk_category: string;
  factors: Record<string, number>;
  rusle_comparison?: Record<string, number>;
}

interface Project {
  id: number;
  name: string;
  status: 'active' | 'completed' | 'planning';
  progress: number;
}

type Section = 'dashboard' | 'calculator' | 'projects' | 'data' | 'analysis' | 'models' | 'settings';

// Debug log after type definitions
console.log('Type definitions loaded');

const app = document.getElementById('app');
if (!app) {
  console.error('Root element not found!');
  throw new Error('Root element not found');
}

// Create Material-UI theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    success: {
      main: '#388e3c',
    },
    warning: {
      main: '#f57c00',
    },
    error: {
      main: '#d32f2f',
    },
    background: {
      default: '#f5f5f5',
    },
  },
});

// API service
const api = {
  calculateErosion: async (data: ErosionInput): Promise<ErosionResult> => {
    try {
      const response = await fetch('http://localhost:8000/api/erosion/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Calculation failed');
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  healthCheck: async () => {
    try {
      const response = await fetch('http://localhost:8000/api/health');
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
};

// Erosion Calculator Component
const ErosionCalculator = () => {
  const [formData, setFormData] = useState({
    rainfall: 1200,
    slope: 15,
    slope_length: 100,
    soil_type: 'loam',
    vegetation_cover: 60,
    support_practices: 50,
    land_use: 'agriculture',
    area: 10,
    seasonality: 'wet'
  });
  
  const [result, setResult] = useState<ErosionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (field: keyof ErosionInput, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError('');
    setResult(null);
  };

  const handleCalculate = async () => {
    setLoading(true);
    setError('');
    try {
      const calculationResult = await api.calculateErosion(formData);
      setResult(calculationResult);
    } catch (err) {
      setError('Calculation failed. Please check your inputs and try again.');
      console.error('Calculation error:', err);
    } finally {
      setLoading(false);
    }
  };

  return React.createElement('div', {
    style: {
      background: 'white',
      padding: '24px',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      marginBottom: '24px'
    }
  }, [
    React.createElement('h3', {
      key: 'calc-title',
      style: { fontSize: '20px', marginBottom: '16px', color: '#333' }
    }, '🧮 Erosion Calculator'),
    
    React.createElement('div', {
      key: 'form-grid',
      style: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '20px'
      }
    }, [
      React.createElement('div', { key: 'rainfall' }, [
        React.createElement('label', {
          key: 'label',
          style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
        }, 'Annual Rainfall (mm):'),
        React.createElement('input', {
          key: 'input',
          type: 'number',
          value: formData.rainfall,
          onChange: (e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('rainfall', parseFloat(e.target.value)),
          style: {
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px'
          }
        })
      ]),
      
      React.createElement('div', { key: 'slope' }, [
        React.createElement('label', {
          key: 'label',
          style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
        }, 'Slope Angle (degrees):'),
        React.createElement('input', {
          key: 'input',
          type: 'number',
          value: formData.slope,
          onChange: (e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('slope', parseFloat(e.target.value)),
          style: {
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px'
          }
        })
      ]),
      
      React.createElement('div', { key: 'length' }, [
        React.createElement('label', {
          key: 'label',
          style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
        }, 'Slope Length (m):'),
        React.createElement('input', {
          key: 'input',
          type: 'number',
          value: formData.slope_length,
          onChange: (e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('slope_length', parseFloat(e.target.value)),
          style: {
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px'
          }
        })
      ]),
      
      React.createElement('div', { key: 'vegetation' }, [
        React.createElement('label', {
          key: 'label',
          style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
        }, 'Vegetation Cover (%):'),
        React.createElement('input', {
          key: 'input',
          type: 'number',
          value: formData.vegetation_cover,
          onChange: (e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('vegetation_cover', parseFloat(e.target.value)),
          min: 0,
          max: 100,
          style: {
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px'
          }
        })
      ]),
      
      React.createElement('div', { key: 'soil' }, [
        React.createElement('label', {
          key: 'label',
          style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
        }, 'Soil Type:'),
        React.createElement('select', {
          key: 'select',
          value: formData.soil_type,
          onChange: (e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('soil_type', e.target.value),
          style: {
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px'
          }
        }, [
          React.createElement('option', { key: 'clay', value: 'clay' }, 'Clay'),
          React.createElement('option', { key: 'loam', value: 'loam' }, 'Loam'),
          React.createElement('option', { key: 'sand', value: 'sand' }, 'Sand'),
          React.createElement('option', { key: 'silt', value: 'silt' }, 'Silt')
        ])
      ]),
      
      React.createElement('div', { key: 'landuse' }, [
        React.createElement('label', {
          key: 'label',
          style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
        }, 'Land Use:'),
        React.createElement('select', {
          key: 'select',
          value: formData.land_use,
          onChange: (e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('land_use', e.target.value),
          style: {
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px'
          }
        }, [
          React.createElement('option', { key: 'agriculture', value: 'agriculture' }, 'Agriculture'),
          React.createElement('option', { key: 'forest', value: 'forest' }, 'Forest'),
          React.createElement('option', { key: 'urban', value: 'urban' }, 'Urban'),
          React.createElement('option', { key: 'grassland', value: 'grassland' }, 'Grassland')
        ])
      ])
    ]),
    
    React.createElement('button', {
      key: 'calculate-btn',
      onClick: handleCalculate,
      disabled: loading,
      style: {
        background: loading ? '#ccc' : theme.palette.primary.main,
        color: 'white',
        border: 'none',
        padding: '12px 24px',
        borderRadius: '8px',
        fontSize: '16px',
        fontWeight: '500',
        cursor: loading ? 'not-allowed' : 'pointer',
        marginBottom: '16px'
      }
    }, loading ? 'Calculating...' : '🧮 Calculate Erosion'),
    
    error && React.createElement('div', {
      key: 'error',
      style: {
        background: '#ffebee',
        color: theme.palette.error.main,
        padding: '12px',
        borderRadius: '4px',
        marginBottom: '16px',
        border: '1px solid #ffcdd2'
      }
    }, `❌ ${error}`),
    
    result && React.createElement('div', {
      key: 'results',
      style: {
        background: '#e8f5e8',
        padding: '20px',
        borderRadius: '8px',
        border: '1px solid #c8e6c9'
      }
    }, [
      React.createElement('h4', {
        key: 'result-title',
        style: { margin: '0 0 16px 0', color: theme.palette.success.main }
      }, '✅ Calculation Results'),
      React.createElement('div', {
        key: 'result-grid',
        style: {
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '12px'
        }
      }, [
        React.createElement('div', { key: 'mean' }, [
          React.createElement('div', {
            key: 'label',
            style: { fontSize: '12px', color: '#666', marginBottom: '4px' }
          }, 'Mean Soil Loss'),
          React.createElement('div', {
            key: 'value',
            style: { fontSize: '18px', fontWeight: 'bold', color: '#333' }
          }, `${result.mean_loss?.toFixed(2) || 'N/A'} t/ha/yr`)
        ]),
        React.createElement('div', { key: 'peak' }, [
          React.createElement('div', {
            key: 'label',
            style: { fontSize: '12px', color: '#666', marginBottom: '4px' }
          }, 'Peak Loss'),
          React.createElement('div', {
            key: 'value',
            style: { fontSize: '18px', fontWeight: 'bold', color: '#333' }
          }, `${result.peak_loss?.toFixed(2) || 'N/A'} t/ha/yr`)
        ]),
        React.createElement('div', { key: 'total' }, [
          React.createElement('div', {
            key: 'label',
            style: { fontSize: '12px', color: '#666', marginBottom: '4px' }
          }, 'Total Soil Loss'),
          React.createElement('div', {
            key: 'value',
            style: { fontSize: '18px', fontWeight: 'bold', color: '#333' }
          }, `${result.total_soil_loss?.toFixed(2) || 'N/A'} tons`)
        ]),
        React.createElement('div', { key: 'risk' }, [
          React.createElement('div', {
            key: 'label',
            style: { fontSize: '12px', color: '#666', marginBottom: '4px' }
          }, 'Risk Category'),
          React.createElement('div', {
            key: 'value',
            style: { 
              fontSize: '16px', 
              fontWeight: 'bold',
              color: result.risk_category === 'high' ? theme.palette.error.main :
                     result.risk_category === 'medium' ? theme.palette.warning.main :
                     theme.palette.success.main
            }
          }, result.risk_category || 'N/A')
        ])
      ])
    ])
  ]);
};

// Main App Component
const TerraSimApp: React.FC = () => {
  const [activeSection, setActiveSection] = useState<Section>('dashboard');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [projects, setProjects] = useState<Project[]>([
    { id: 1, name: 'Watershed Alpha', status: 'active', progress: 75 },
    { id: 2, name: 'Coastal Study Beta', status: 'completed', progress: 100 },
    { id: 3, name: 'Mountain Region Gamma', status: 'planning', progress: 25 }
  ]);

  // Check backend connection
  useEffect(() => {
    const checkBackend = async () => {
      const isHealthy = await api.healthCheck();
      setBackendStatus(isHealthy ? 'connected' : 'disconnected');
    };
    checkBackend();
    const interval = setInterval(checkBackend, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const handleNavClick = (section: Section) => {
    setActiveSection(section);
  };

  const menuItems = [
    { id: 'dashboard' as Section, text: 'Dashboard', icon: '📊' },
    { id: 'calculator' as Section, text: 'Erosion Calculator', icon: '🧮' },
    { id: 'projects' as Section, text: 'Projects', icon: '📁' },
    { id: 'data' as Section, text: 'Data Upload', icon: '☁️' },
    { id: 'analysis' as Section, text: 'Analysis', icon: '📈' },
    { id: 'models' as Section, text: 'Models', icon: '🤖' },
    { id: 'settings' as Section, text: 'Settings', icon: '⚙️' }
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'calculator':
        return React.createElement('div', { key: 'calculator-content' }, [
          React.createElement('h2', {
            key: 'title',
            style: { fontSize: '32px', marginBottom: '8px', color: '#333' }
          }, '🧮 Erosion Calculator'),
          React.createElement('p', {
            key: 'subtitle',
            style: { fontSize: '16px', marginBottom: '32px', color: '#666' }
          }, 'Calculate soil erosion using the TerraSim advanced model with real backend processing.'),
          React.createElement(ErosionCalculator, { key: 'calculator' })
        ]);
        
      case 'projects':
        return React.createElement('div', { key: 'projects-content' }, [
          React.createElement('h2', {
            key: 'title',
            style: { fontSize: '32px', marginBottom: '8px', color: '#333' }
          }, '📁 Projects'),
          React.createElement('p', {
            key: 'subtitle',
            style: { fontSize: '16px', marginBottom: '32px', color: '#666' }
          }, 'Manage your erosion modeling projects.'),
          React.createElement('div', {
            key: 'projects-list',
            style: {
              display: 'grid',
              gap: '16px'
            }
          }, projects.map(project => 
            React.createElement('div', {
              key: project.id,
              style: {
                background: 'white',
                padding: '20px',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }
            }, [
              React.createElement('div', { key: 'info' }, [
                React.createElement('h3', {
                  key: 'name',
                  style: { margin: '0 0 8px 0', fontSize: '18px' }
                }, project.name),
                React.createElement('div', {
                  key: 'status',
                  style: {
                    fontSize: '14px',
                    color: project.status === 'completed' ? theme.palette.success.main :
                           project.status === 'active' ? theme.palette.primary.main :
                           '#666'
                  }
                }, `Status: ${project.status}`)
              ]),
              React.createElement('div', { key: 'progress' }, [
                React.createElement('div', {
                  key: 'bar-bg',
                  style: {
                    width: '100px',
                    height: '8px',
                    background: '#e0e0e0',
                    borderRadius: '4px',
                    marginBottom: '4px'
                  }
                }),
                React.createElement('div', {
                  key: 'bar-fill',
                  style: {
                    width: `${project.progress}%`,
                    height: '8px',
                    background: theme.palette.primary.main,
                    borderRadius: '4px',
                    marginTop: '-12px'
                  }
                }),
                React.createElement('div', {
                  key: 'percent',
                  style: { fontSize: '12px', textAlign: 'center', color: '#666' }
                }, `${project.progress}%`)
              ])
            ])
          ))
        ]);
        
      default:
        return React.createElement('div', { key: 'dashboard-content' }, [
          React.createElement('h2', {
            key: 'title',
            style: { fontSize: '32px', marginBottom: '8px', color: '#333' }
          }, '📊 Dashboard'),
          React.createElement('p', {
            key: 'subtitle',
            style: { fontSize: '16px', marginBottom: '32px', color: '#666' }
          }, 'Welcome to TerraSim! Your advanced GIS erosion modeling platform.'),
          
          React.createElement('div', {
            key: 'status-bar',
            style: {
              background: backendStatus === 'connected' ? '#e8f5e8' : '#fff3e0',
              padding: '16px',
              borderRadius: '8px',
              marginBottom: '32px',
              border: `1px solid ${backendStatus === 'connected' ? '#c8e6c9' : '#ffcc02'}`
            }
          }, [
            React.createElement('div', {
              key: 'status-text',
              style: {
                display: 'flex',
                alignItems: 'center',
                fontSize: '14px'
              }
            }, [
              React.createElement('span', {
                key: 'status-icon',
                style: { marginRight: '8px' }
              }, backendStatus === 'connected' ? '✅' : '⚠️'),
              React.createElement('span', {
                key: 'status-message',
                style: {
                  color: backendStatus === 'connected' ? theme.palette.success.main : theme.palette.warning.main
                }
              }, `Backend Status: ${backendStatus === 'connected' ? 'Connected' : 'Disconnected'}`)
            ])
          ]),
          
          React.createElement('div', {
            key: 'stats-grid',
            style: {
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '20px',
              marginBottom: '32px'
            }
          }, [
            React.createElement('div', {
              key: 'stat-1',
              style: {
                background: 'white',
                padding: '24px',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }
            }, [
              React.createElement('div', {
                key: 'stat-1-header',
                style: { display: 'flex', alignItems: 'center', marginBottom: '16px' }
              }, [
                React.createElement('span', {
                  key: 'stat-1-icon',
                  style: { fontSize: '24px', marginRight: '12px' }
                }, '📁'),
                React.createElement('h3', {
                  key: 'stat-1-title',
                  style: { margin: 0, fontSize: '18px', color: '#333' }
                }, 'Projects')
              ]),
              React.createElement('div', {
                key: 'stat-1-value',
                style: { fontSize: '36px', fontWeight: 'bold', color: theme.palette.primary.main }
              }, projects.length.toString())
            ]),
            React.createElement('div', {
              key: 'stat-2',
              style: {
                background: 'white',
                padding: '24px',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }
            }, [
              React.createElement('div', {
                key: 'stat-2-header',
                style: { display: 'flex', alignItems: 'center', marginBottom: '16px' }
              }, [
                React.createElement('span', {
                  key: 'stat-2-icon',
                  style: { fontSize: '24px', marginRight: '12px', color: '#388e3c' }
                }, '☁️'),
                React.createElement('h3', {
                  key: 'stat-2-title',
                  style: { margin: 0, fontSize: '18px', color: '#333' }
                }, 'Datasets')
              ]),
              React.createElement('div', {
                key: 'stat-2-value',
                style: { fontSize: '36px', fontWeight: 'bold', color: '#388e3c' }
              }, '48')
            ]),
            React.createElement('div', {
              key: 'stat-3',
              style: {
                background: 'white',
                padding: '24px',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }
            }, [
              React.createElement('div', {
                key: 'stat-3-header',
                style: { display: 'flex', alignItems: 'center', marginBottom: '16px' }
              }, [
                React.createElement('span', {
                  key: 'stat-3-icon',
                  style: { fontSize: '24px', marginRight: '12px', color: '#f57c00' }
                }, '📈'),
                React.createElement('h3', {
                  key: 'stat-3-title',
                  style: { margin: 0, fontSize: '18px', color: '#333' }
                }, 'Analyses')
              ]),
              React.createElement('div', {
                key: 'stat-3-value',
                style: { fontSize: '36px', fontWeight: 'bold', color: '#f57c00' }
              }, '23')
            ]),
            React.createElement('div', {
              key: 'stat-4',
              style: {
                background: 'white',
                padding: '24px',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }
            }, [
              React.createElement('div', {
                key: 'stat-4-header',
                style: { display: 'flex', alignItems: 'center', marginBottom: '16px' }
              }, [
                React.createElement('span', {
                  key: 'stat-4-icon',
                  style: { fontSize: '24px', marginRight: '12px', color: '#d32f2f' }
                }, '⚙️'),
                React.createElement('h3', {
                  key: 'stat-4-title',
                  style: { margin: 0, fontSize: '18px', color: '#333' }
                }, 'Active Jobs')
              ]),
              React.createElement('div', {
                key: 'stat-4-value',
                style: { fontSize: '36px', fontWeight: 'bold', color: '#d32f2f' }
              }, '7')
            ])
          ]),
          
          React.createElement('div', {
            key: 'quick-actions',
            style: {
              background: 'white',
              padding: '24px',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }
          }, [
            React.createElement('h3', {
              key: 'actions-title',
              style: { margin: '0 0 16px 0', fontSize: '18px', color: '#333' }
            }, '🚀 Quick Actions'),
            React.createElement('div', {
              key: 'actions-grid',
              style: {
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '12px'
              }
            }, [
              React.createElement('button', {
                key: 'new-project',
                onClick: () => handleNavClick('calculator'),
                style: {
                  background: theme.palette.primary.main,
                  color: 'white',
                  border: 'none',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: 'pointer'
                }
              }, '🧮 New Calculation'),
              React.createElement('button', {
                key: 'upload-data',
                onClick: () => handleNavClick('data'),
                style: {
                  background: theme.palette.success.main,
                  color: 'white',
                  border: 'none',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: 'pointer'
                }
              }, '☁️ Upload Data'),
              React.createElement('button', {
                key: 'view-analysis',
                onClick: () => handleNavClick('analysis'),
                style: {
                  background: theme.palette.warning.main,
                  color: 'white',
                  border: 'none',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: 'pointer'
                }
              }, '📈 View Analysis')
            ])
          ])
        ]);
    }
  };

  return React.createElement('div', {
    style: {
      height: '100vh',
      background: theme.palette.background.default,
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif'
    }
  }, [
    React.createElement('header', {
      key: 'header',
      style: {
        background: theme.palette.primary.main,
        color: 'white',
        padding: '20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }
    }, [
      React.createElement('h1', {
        key: 'title',
        style: { margin: 0, fontSize: '24px' }
      }, 'TerraSim'),
      React.createElement('div', {
        key: 'user-info',
        style: {
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }
      }, [
        React.createElement('span', {
          key: 'backend-indicator',
          style: {
            fontSize: '12px',
            padding: '4px 8px',
            borderRadius: '12px',
            background: backendStatus === 'connected' ? '#4caf50' : '#ff9800'
          }
        }, backendStatus === 'connected' ? '🟢 API Connected' : '🟡 API Disconnected'),
        React.createElement('div', {
          key: 'user',
          style: {
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: theme.palette.secondary.main,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '14px'
          }
        }, 'D')
      ])
    ]),
    React.createElement('div', {
      key: 'content',
      style: {
        display: 'flex',
        height: 'calc(100vh - 64px)'
      }
    }, [
      React.createElement('nav', {
        key: 'sidebar',
        style: {
          width: '280px',
          background: 'white',
          borderRight: '1px solid #e0e0e0',
          padding: '20px 0'
        }
      }, menuItems.map(item => 
        React.createElement('div', {
          key: item.id,
          onClick: () => handleNavClick(item.id),
          style: {
            padding: '12px 20px',
            cursor: 'pointer',
            background: activeSection === item.id ? theme.palette.primary.main : 'transparent',
            color: activeSection === item.id ? 'white' : '#333',
            transition: 'all 0.2s ease'
          }
        }, `${item.icon} ${item.text}`)
      )),
      React.createElement('main', {
        key: 'main',
        style: {
          flex: 1,
          padding: '40px',
          overflow: 'auto'
        }
      }, renderContent())
    ])
  ]);
};

console.log('Rendering functional TerraSim app...');
const root = createRoot(app);
root.render(
  React.createElement(
    ThemeProvider,
    { theme },
    React.createElement(
      CssBaseline,
      null,
      React.createElement(TerraSimApp)
    )
  )
);
console.log('Functional TerraSim app rendered successfully!');
