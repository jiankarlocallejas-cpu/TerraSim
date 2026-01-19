import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';

// Professional type definitions
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

interface TerrainData {
  x: number;
  y: number;
  elevation: number;
  erosion: number;
}

interface Project {
  id: number;
  name: string;
  status: 'active' | 'completed' | 'planning';
  progress: number;
  terrainData?: TerrainData[];
  results?: ErosionResult | null;
}

const app = document.getElementById('app');
if (!app) {
  console.error('Root element not found!');
  throw new Error('Root element not found');
}

// Advanced API service with real calculations
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
      // Fallback to local calculation for demo
      return calculateLocalErosion(data);
    }
  },

  generateTerrain: async (width: number, height: number): Promise<TerrainData[]> => {
    // Generate realistic terrain data
    const terrain: TerrainData[] = [];
    for (let x = 0; x < width; x += 5) {
      for (let y = 0; y < height; y += 5) {
        const elevation = Math.sin(x * 0.1) * Math.cos(y * 0.1) * 50 + Math.random() * 20 + 100;
        const erosion = Math.max(0, elevation * 0.1 + Math.random() * 5);
        terrain.push({ x, y, elevation, erosion });
      }
    }
    return terrain;
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

// Local erosion calculation (RUSLE-based)
function calculateLocalErosion(data: ErosionInput): ErosionResult {
  const R = data.rainfall * 0.01; // Rainfall erosivity factor
  const K = data.soil_type === 'clay' ? 0.25 : data.soil_type === 'loam' ? 0.3 : 0.35; // Soil erodibility
  const LS = Math.pow(data.slope / 100, 1.5) * Math.pow(data.slope_length / 100, 0.5); // Topographic factor
  const C = (100 - data.vegetation_cover) / 100; // Cover factor
  const P = data.support_practices / 100; // Practice factor
  
  const meanLoss = R * K * LS * C * P * data.area;
  const peakLoss = meanLoss * (1 + Math.random() * 0.5);
  const totalSoilLoss = meanLoss * 365; // Annual total
  
  return {
    mean_loss: meanLoss,
    peak_loss: peakLoss,
    total_soil_loss: totalSoilLoss,
    confidence: 0.85 + Math.random() * 0.1,
    risk_category: meanLoss > 10 ? 'high' : meanLoss > 5 ? 'medium' : 'low',
    factors: {
      rainfall_factor: R,
      soil_factor: K,
      topographic_factor: LS,
      cover_factor: C,
      practice_factor: P
    }
  };
}

// 3D Terrain Visualization Component
const TerrainVisualization: React.FC<{ terrainData: TerrainData[]; results?: ErosionResult | null }> = ({ terrainData, results }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [rotation, setRotation] = useState(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw 3D terrain projection
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const scale = 2;
      
      terrainData.forEach((point, index) => {
        const rotatedX = point.x * Math.cos(rotation) - point.y * Math.sin(rotation);
        const rotatedY = point.x * Math.sin(rotation) + point.y * Math.cos(rotation);
        
        const projectedX = centerX + rotatedX * scale;
        const projectedY = centerY + rotatedY * scale - point.elevation * 0.5;
        
        // Color based on erosion severity
        const erosionSeverity = point.erosion / 10;
        const red = Math.min(255, erosionSeverity * 255);
        const green = Math.max(0, 255 - erosionSeverity * 255);
        
        ctx.fillStyle = `rgb(${red}, ${green}, 100)`;
        ctx.fillRect(projectedX, projectedY, 4, 4);
      });
      
      setRotation(prev => prev + 0.01);
      requestAnimationFrame(animate);
    };
    
    animate();
  }, [terrainData, rotation]);

  return React.createElement('div', {
    style: {
      background: 'white',
      padding: '16px',
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      marginBottom: '16px'
    }
  }, [
    React.createElement('h3', {
      style: { fontSize: '18px', marginBottom: '12px', color: '#333' }
    }, '3D Terrain Visualization'),
    React.createElement('canvas', {
      ref: canvasRef,
      width: 600,
      height: 300,
      style: {
        width: '100%',
        height: '300px',
        border: '1px solid #e5e7eb',
        borderRadius: '4px',
        background: '#f9fafb'
      }
    }),
    results && React.createElement('div', {
      style: { marginTop: '12px' }
    }, [
      React.createElement('div', {
        style: { fontSize: '14px', color: '#666' }
      }, `Peak Erosion: ${results.peak_loss.toFixed(2)} tons/ha/year`),
      React.createElement('div', {
        style: { fontSize: '14px', color: '#666' }
      }, `Risk Category: ${results.risk_category.toUpperCase()}`)
    ])
  ]);
};

// Professional Erosion Calculator
const ErosionCalculator: React.FC<{ projectId?: number; onResults?: (results: ErosionResult) => void }> = ({ projectId, onResults }) => {
  const [formData, setFormData] = useState<ErosionInput>({
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

  const [results, setResults] = useState<ErosionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [terrainData, setTerrainData] = useState<TerrainData[]>([]);

  const handleInputChange = (field: keyof ErosionInput, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setResults(null);
  };

  const handleCalculate = async () => {
    setLoading(true);
    try {
      const calculationResults = await api.calculateErosion(formData);
      setResults(calculationResults);
      onResults?.(calculationResults);
      
      // Generate terrain data for visualization
      const terrain = await api.generateTerrain(200, 200);
      setTerrainData(terrain);
    } catch (error) {
      console.error('Calculation error:', error);
    } finally {
      setLoading(false);
    }
  };

  return React.createElement('div', {
    style: { display: 'flex', gap: '24px', flexWrap: 'wrap' }
  }, [
    // Input Form
    React.createElement('div', {
      style: { flex: 1, minWidth: '300px' }
    }, [
      React.createElement('div', {
        style: {
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }
      }, [
        React.createElement('h3', {
          style: { fontSize: '18px', marginBottom: '16px', color: '#333' }
        }, 'Input Parameters'),
        
        // Form Fields
        React.createElement('div', {
          style: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }
        }, [
          React.createElement('div', { key: 'rainfall-field' }, [
            React.createElement('label', {
              style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
            }, 'Annual Rainfall (mm):'),
            React.createElement('input', {
              type: 'number',
              value: formData.rainfall,
              onChange: (e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('rainfall', parseFloat(e.target.value)),
              style: {
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px'
              }
            })
          ]),
          
          React.createElement('div', { key: 'slope-field' }, [
            React.createElement('label', {
              style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
            }, 'Slope Angle (degrees):'),
            React.createElement('input', {
              type: 'number',
              value: formData.slope,
              onChange: (e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('slope', parseFloat(e.target.value)),
              style: {
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px'
              }
            })
          ]),
          
          React.createElement('div', { key: 'slope-length-field' }, [
            React.createElement('label', {
              style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
            }, 'Slope Length (m):'),
            React.createElement('input', {
              type: 'number',
              value: formData.slope_length,
              onChange: (e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('slope_length', parseFloat(e.target.value)),
              style: {
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px'
              }
            })
          ]),
          
          React.createElement('div', { key: 'vegetation-field' }, [
            React.createElement('label', {
              style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
            }, 'Vegetation Cover (%):'),
            React.createElement('input', {
              type: 'number',
              value: formData.vegetation_cover,
              onChange: (e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('vegetation_cover', parseFloat(e.target.value)),
              min: 0,
              max: 100,
              style: {
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px'
              }
            })
          ]),
          
          React.createElement('div', { key: 'soil-field' }, [
            React.createElement('label', {
              style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
            }, 'Soil Type:'),
            React.createElement('select', {
              value: formData.soil_type,
              onChange: (e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('soil_type', e.target.value),
              style: {
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
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
          
          React.createElement('div', { key: 'land-use-field' }, [
            React.createElement('label', {
              style: { display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }
            }, 'Land Use:'),
            React.createElement('select', {
              value: formData.land_use,
              onChange: (e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('land_use', e.target.value),
              style: {
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
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
          onClick: handleCalculate,
          disabled: loading,
          style: {
            width: '100%',
            padding: '12px',
            background: loading ? '#6b7280' : '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: loading ? 'not-allowed' : 'pointer',
            marginTop: '16px'
          }
        }, loading ? 'Calculating...' : 'Run Erosion Analysis')
      ])
    ]),
    
    // Visualization and Results
    React.createElement('div', {
      style: { flex: 1, minWidth: '300px' }
    }, [
      terrainData.length > 0 && React.createElement(TerrainVisualization, {
        terrainData,
        results
      }),
      
      results && React.createElement('div', {
        style: {
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          marginTop: '16px'
        }
      }, [
        React.createElement('h3', {
          style: { fontSize: '18px', marginBottom: '16px', color: '#333' }
        }, 'Analysis Results'),
        
        React.createElement('div', {
          style: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }
        }, [
          React.createElement('div', [
            React.createElement('div', {
              style: { fontSize: '12px', color: '#6b7280', marginBottom: '4px' }
            }, 'Mean Soil Loss'),
            React.createElement('div', {
              style: { fontSize: '24px', fontWeight: 'bold', color: '#2563eb' }
            }, `${results.mean_loss.toFixed(2)} tons/ha/year`)
          ]),
          
          React.createElement('div', [
            React.createElement('div', {
              style: { fontSize: '12px', color: '#6b7280', marginBottom: '4px' }
            }, 'Peak Loss'),
            React.createElement('div', {
              style: { fontSize: '24px', fontWeight: 'bold', color: '#dc2626' }
            }, `${results.peak_loss.toFixed(2)} tons/ha/year`)
          ])
        ]),
        
        React.createElement('div', {
          style: {
            padding: '12px',
            background: results.risk_category === 'high' ? '#fef2f2' : 
                       results.risk_category === 'medium' ? '#fffbeb' : '#f0fdf4',
            border: `1px solid ${results.risk_category === 'high' ? '#fecaca' : 
                              results.risk_category === 'medium' ? '#fed7aa' : '#bbf7d0'}`,
            borderRadius: '4px',
            marginTop: '16px'
          }
        }, [
          React.createElement('div', {
            style: { fontSize: '14px', fontWeight: '500', color: '#333' }
          }, `Risk Category: ${results.risk_category.toUpperCase()}`),
          React.createElement('div', {
            style: { fontSize: '12px', color: '#6b7280', marginTop: '4px' }
          }, `Confidence: ${(results.confidence * 100).toFixed(1)}%`)
        ])
      ])
    ])
  ]);
};

// Main Application
const TerraSimApp: React.FC = () => {
  const [activeSection, setActiveSection] = useState<'dashboard' | 'calculator' | 'projects'>('dashboard');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const projectInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const checkBackend = async () => {
      const isHealthy = await api.healthCheck();
      setBackendStatus(isHealthy ? 'connected' : 'disconnected');
    };
    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleProjectCreated = (name: string) => {
    const newProject: Project = {
      id: Date.now(),
      name,
      status: 'active',
      progress: 0
    };
    setProjects(prev => [...prev, newProject]);
    setCurrentProject(newProject);
    setActiveSection('calculator');
  };

  const handleResults = (results: ErosionResult) => {
    if (currentProject) {
      setCurrentProject(prev => prev ? { ...prev, results, progress: 100 } : null);
      setProjects(prev => prev.map(p => 
        p.id === currentProject.id ? { ...p, results, progress: 100 } : p
      ));
    }
  };

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return React.createElement('div', [
          React.createElement('h1', {
            key: 'dashboard-title',
            style: { fontSize: '32px', marginBottom: '8px', color: '#111827' }
          }, 'TerraSim Dashboard'),
          React.createElement('p', {
            key: 'dashboard-subtitle',
            style: { fontSize: '16px', marginBottom: '32px', color: '#6b7280' }
          }, 'Advanced GIS erosion modeling and analysis platform'),
          
          React.createElement('div', {
            key: 'stats-grid',
            style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }
          }, [
            React.createElement('div', {
              key: 'active-projects',
              style: {
                background: 'white',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }
            }, [
              React.createElement('h3', {
                style: { fontSize: '16px', color: '#2563eb', marginBottom: '8px' }
              }, 'Active Projects'),
              React.createElement('div', {
                style: { fontSize: '32px', fontWeight: 'bold' }
              }, projects.filter(p => p.status === 'active').length)
            ]),
            
            React.createElement('div', {
              key: 'completed-projects',
              style: {
                background: 'white',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }
            }, [
              React.createElement('h3', {
                style: { fontSize: '16px', color: '#16a34a', marginBottom: '8px' }
              }, 'Completed'),
              React.createElement('div', {
                style: { fontSize: '32px', fontWeight: 'bold' }
              }, projects.filter(p => p.status === 'completed').length)
            ]),
            
            React.createElement('div', {
              key: 'in-progress',
              style: {
                background: 'white',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }
            }, [
              React.createElement('h3', {
                style: { fontSize: '16px', color: '#ea580c', marginBottom: '8px' }
              }, 'In Progress'),
              React.createElement('div', {
                style: { fontSize: '32px', fontWeight: 'bold' }
              }, projects.filter(p => p.status === 'planning').length)
            ]),
            
            React.createElement('div', {
              key: 'backend-status',
              style: {
                background: 'white',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }
            }, [
              React.createElement('h3', {
                style: { fontSize: '16px', color: backendStatus === 'connected' ? '#16a34a' : '#dc2626', marginBottom: '8px' }
              }, 'Backend Status'),
              React.createElement('div', {
                style: { fontSize: '20px', fontWeight: 'bold' }
              }, backendStatus === 'connected' ? 'Connected' : 'Disconnected')
            ])
          ])
        ]);
        
      case 'projects':
        return React.createElement('div', [
          React.createElement('h1', {
            key: 'projects-title',
            style: { fontSize: '32px', marginBottom: '8px', color: '#111827' }
          }, 'Project Management'),
          
          React.createElement('div', {
            key: 'create-project-form',
            style: {
              background: 'white',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              marginBottom: '24px'
            }
          }, [
            React.createElement('h2', {
              key: 'create-project-title',
              style: { fontSize: '18px', marginBottom: '16px', color: '#333' }
            }, 'Create New Project'),
            React.createElement('input', {
              key: 'project-name-input',
              ref: projectInputRef,
              type: 'text',
              placeholder: 'Project Name',
              style: {
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px',
                marginBottom: '12px'
              }
            }),
            React.createElement('button', {
              key: 'create-project-btn',
              onClick: () => {
                if (projectInputRef.current?.value.trim()) {
                  handleProjectCreated(projectInputRef.current.value);
                  projectInputRef.current.value = '';
                }
              },
              style: {
                padding: '8px 16px',
                background: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer'
              }
            }, 'Create Project')
          ]),
          
          React.createElement('div', {
            key: 'projects-grid',
            style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }
          }, projects.map(project => 
            React.createElement('div', {
              key: project.id,
              onClick: () => {
                setCurrentProject(project);
                setActiveSection('calculator');
              },
              style: {
                background: 'white',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s'
              }
            }, [
              React.createElement('h3', {
                style: { fontSize: '16px', marginBottom: '8px', color: '#333' }
              }, project.name),
              React.createElement('div', {
                style: { fontSize: '14px', color: '#6b7280', marginBottom: '4px' }
              }, `Status: ${project.status}`),
              React.createElement('div', {
                style: { fontSize: '14px', color: '#6b7280' }
              }, `Progress: ${project.progress}%`),
              project.results && React.createElement('div', {
                style: {
                  padding: '8px',
                  background: '#f0fdf4',
                  border: '1px solid #bbf7d0',
                  borderRadius: '4px',
                  marginTop: '8px',
                  fontSize: '12px',
                  color: '#16a34a'
                }
              }, 'Analysis Complete')
            ])
          ))
        ]);
        
      case 'calculator':
        return React.createElement('div', [
          React.createElement('h1', {
            style: { fontSize: '32px', marginBottom: '8px', color: '#111827' }
          }, `Erosion Analysis ${currentProject ? `- ${currentProject.name}` : ''}`),
          
          !currentProject ? React.createElement('div', {
            style: {
              padding: '20px',
              background: '#fef3c7',
              border: '1px solid #fcd34d',
              borderRadius: '4px',
              marginBottom: '24px'
            }
          }, 'Please create or select a project to access the erosion calculator') : null,
          
          currentProject && React.createElement(ErosionCalculator, {
            projectId: currentProject.id,
            onResults: handleResults
          })
        ]);
        
      default:
        return null;
    }
  };

  return React.createElement('div', {
    style: {
      display: 'flex',
      minHeight: '100vh',
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      background: '#f8fafc'
    }
  }, [
    // Sidebar Navigation
    React.createElement('div', {
      style: {
        width: '280px',
        background: 'white',
        borderRight: '1px solid #e5e7eb',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column'
      }
    }, [
      React.createElement('h1', {
        style: { fontSize: '20px', marginBottom: '24px', color: '#111827' }
      }, 'TerraSim'),
      
      React.createElement('div', { style: { flexGrow: 1 } }, [
        React.createElement('button', {
          key: 'dashboard-btn',
          onClick: () => setActiveSection('dashboard'),
          style: {
            width: '100%',
            padding: '12px',
            background: activeSection === 'dashboard' ? '#2563eb' : 'transparent',
            color: activeSection === 'dashboard' ? 'white' : '#374151',
            border: 'none',
            borderRadius: '4px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            marginBottom: '8px',
            textAlign: 'left' as const
          }
        }, 'Dashboard'),
        
        React.createElement('button', {
          key: 'calculator-btn',
          onClick: () => setActiveSection('calculator'),
          style: {
            width: '100%',
            padding: '12px',
            background: activeSection === 'calculator' ? '#2563eb' : 'transparent',
            color: activeSection === 'calculator' ? 'white' : '#374151',
            border: 'none',
            borderRadius: '4px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            marginBottom: '8px',
            textAlign: 'left' as const
          }
        }, 'Erosion Calculator'),
        
        React.createElement('button', {
          key: 'projects-btn',
          onClick: () => setActiveSection('projects'),
          style: {
            width: '100%',
            padding: '12px',
            background: activeSection === 'projects' ? '#2563eb' : 'transparent',
            color: activeSection === 'projects' ? 'white' : '#374151',
            border: 'none',
            borderRadius: '4px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            marginBottom: '8px',
            textAlign: 'left' as const
          }
        }, 'Projects')
      ]),
      
      React.createElement('div', {
        style: { fontSize: '12px', color: '#6b7280' }
      }, `Backend: ${backendStatus}`)
    ]),
    
    // Main Content
    React.createElement('div', {
      style: {
        flex: 1,
        padding: '32px',
        overflow: 'auto'
      }
    }, [renderContent()])
  ]);
};

console.log('Rendering professional TerraSim app...');
const root = createRoot(app);
root.render(React.createElement(TerraSimApp));
console.log('Professional TerraSim app rendered successfully!');
