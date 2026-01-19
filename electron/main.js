/**
 * TerraSim Electron Main Process
 * Cross-platform desktop application wrapper
 */

const { app, BrowserWindow, Menu, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs').promises;
const axios = require('axios');
const { spawn } = require('child_process');

// Keep a global reference of the window object
let mainWindow;
let pythonProcess;
let serverProcess;

// Development mode flag
const isDev = process.env.NODE_ENV === 'development';

class TerraSimElectron {
  constructor() {
    this.init();
  }

  async init() {
    // Set app user model id for Windows
    if (process.platform === 'win32') {
      app.setAppUserModelId('com.terrasim.desktop');
    }

    // App event handlers
    app.whenReady().then(() => {
      this.createWindow();
      this.setupMenu();
      this.startBackend();
      this.setupIpcHandlers();
    });

    app.on('window-all-closed', () => {
      // On macOS, keep app running even when all windows are closed
      if (process.platform !== 'darwin') {
        this.cleanup();
        app.quit();
      }
    });

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        this.createWindow();
      }
    });

    app.on('before-quit', () => {
      this.cleanup();
    });
  }

  createWindow() {
    // Create the browser window
    mainWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      minWidth: 1200,
      minHeight: 800,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        preload: path.join(__dirname, 'preload.js')
      },
      icon: path.join(__dirname, 'assets/icon.png'),
      show: false,
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default'
    });

    // Load the app
    const startUrl = isDev 
      ? 'http://localhost:3000' 
      : `file://${path.join(__dirname, '../frontend/dist/index.html')}`;
    
    mainWindow.loadURL(startUrl);

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
      mainWindow.show();
      
      if (isDev) {
        mainWindow.webContents.openDevTools();
      }
    });

    // Handle window closed
    mainWindow.on('closed', () => {
      mainWindow = null;
    });

    // Handle external links
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
      shell.openExternal(url);
      return { action: 'deny' };
    });
  }

  setupMenu() {
    const template = [
      {
        label: 'File',
        submenu: [
          {
            label: 'New Project',
            accelerator: 'CmdOrCtrl+N',
            click: () => {
              mainWindow.webContents.send('menu:new-project');
            }
          },
          {
            label: 'Open Project',
            accelerator: 'CmdOrCtrl+O',
            click: async () => {
              const result = await dialog.showOpenDialog(mainWindow, {
                properties: ['openFile'],
                filters: [
                  { name: 'TerraSim Projects', extensions: ['terrasim'] },
                  { name: 'JSON Files', extensions: ['json'] },
                  { name: 'All Files', extensions: ['*'] }
                ]
              });

              if (!result.canceled) {
                mainWindow.webContents.send('menu:open-project', result.filePaths[0]);
              }
            }
          },
          {
            label: 'Save Project',
            accelerator: 'CmdOrCtrl+S',
            click: async () => {
              const result = await dialog.showSaveDialog(mainWindow, {
                filters: [
                  { name: 'TerraSim Projects', extensions: ['terrasim'] },
                  { name: 'JSON Files', extensions: ['json'] }
                ]
              });

              if (!result.canceled) {
                mainWindow.webContents.send('menu:save-project', result.filePath);
              }
            }
          },
          { type: 'separator' },
          {
            label: 'Import GIS Data',
            accelerator: 'CmdOrCtrl+I',
            click: async () => {
              const result = await dialog.showOpenDialog(mainWindow, {
                properties: ['openFile', 'multiSelections'],
                filters: [
                  { name: 'Shapefile', extensions: ['shp'] },
                  { name: 'GeoJSON', extensions: ['geojson', 'json'] },
                  { name: 'Raster Files', extensions: ['tif', 'tiff', 'img', 'dem'] },
                  { name: 'CSV Files', extensions: ['csv'] },
                  { name: 'All Supported', extensions: ['shp', 'geojson', 'json', 'tif', 'tiff', 'img', 'dem', 'csv'] }
                ]
              });

              if (!result.canceled) {
                mainWindow.webContents.send('menu:import-data', result.filePaths);
              }
            }
          },
          {
            label: 'Export Results',
            accelerator: 'CmdOrCtrl+E',
            click: async () => {
              const result = await dialog.showSaveDialog(mainWindow, {
                filters: [
                  { name: 'PDF Report', extensions: ['pdf'] },
                  { name: 'CSV Data', extensions: ['csv'] },
                  { name: 'GeoJSON', extensions: ['geojson'] },
                  { name: 'JSON', extensions: ['json'] }
                ]
              });

              if (!result.canceled) {
                mainWindow.webContents.send('menu:export-results', result.filePath);
              }
            }
          },
          { type: 'separator' },
          {
            label: 'Exit',
            accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
            click: () => {
              app.quit();
            }
          }
        ]
      },
      {
        label: 'Edit',
        submenu: [
          { label: 'Undo', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
          { label: 'Redo', accelerator: 'Shift+CmdOrCtrl+Z', role: 'redo' },
          { type: 'separator' },
          { label: 'Cut', accelerator: 'CmdOrCtrl+X', role: 'cut' },
          { label: 'Copy', accelerator: 'CmdOrCtrl+C', role: 'copy' },
          { label: 'Paste', accelerator: 'CmdOrCtrl+V', role: 'paste' }
        ]
      },
      {
        label: 'View',
        submenu: [
          { label: 'Reload', accelerator: 'CmdOrCtrl+R', role: 'reload' },
          { label: 'Force Reload', accelerator: 'CmdOrCtrl+Shift+R', role: 'forceReload' },
          { label: 'Toggle Developer Tools', accelerator: 'F12', role: 'toggleDevTools' },
          { label: 'Toggle Full Screen', accelerator: 'F11', role: 'togglefullscreen' },
          { type: 'separator' },
          { label: 'Zoom In', accelerator: 'CmdOrCtrl+Plus', role: 'zoomIn' },
          { label: 'Zoom Out', accelerator: 'CmdOrCtrl+-', role: 'zoomOut' },
          { label: 'Reset Zoom', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' }
        ]
      },
      {
        label: 'Tools',
        submenu: [
          {
            label: 'Erosion Analysis',
            accelerator: 'CmdOrCtrl+Shift+E',
            click: () => {
              mainWindow.webContents.send('menu:erosion-analysis');
            }
          },
          {
            label: 'GIS Processing',
            accelerator: 'CmdOrCtrl+Shift+G',
            click: () => {
              mainWindow.webContents.send('menu:gis-processing');
            }
          },
          {
            label: 'Data Validation',
            accelerator: 'CmdOrCtrl+Shift+V',
            click: () => {
              mainWindow.webContents.send('menu:data-validation');
            }
          },
          { type: 'separator' },
          {
            label: 'Settings',
            accelerator: 'CmdOrCtrl+,',
            click: () => {
              mainWindow.webContents.send('menu:settings');
            }
          }
        ]
      },
      {
        label: 'Window',
        submenu: [
          { label: 'Minimize', accelerator: 'CmdOrCtrl+M', role: 'minimize' },
          { label: 'Close', accelerator: 'CmdOrCtrl+W', role: 'close' }
        ]
      },
      {
        label: 'Help',
        submenu: [
          {
            label: 'Documentation',
            click: () => {
              shell.openExternal('https://terrasim.docs.com');
            }
          },
          {
            label: 'Report Issue',
            click: () => {
              shell.openExternal('https://github.com/terrasim/issues');
            }
          },
          { type: 'separator' },
          {
            label: 'About TerraSim',
            click: () => {
              dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'About TerraSim',
                message: 'TerraSim v2.0.0',
                detail: 'Advanced GIS Erosion Modeling Platform\n\n' +
                       'Built with Electron, Python, and modern web technologies\n\n' +
                       '© 2024 TerraSim Team'
              });
            }
          }
        ]
      }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
  }

  async startBackend() {
    try {
      // Start Python backend server
      const pythonScript = path.join(__dirname, '../backend/main.py');
      
      pythonProcess = spawn('python', [pythonScript], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONPATH: path.join(__dirname, '../backend') }
      });

      pythonProcess.stdout.on('data', (data) => {
        console.log(`Python stdout: ${data}`);
        // Notify renderer when server is ready
        if (data.toString().includes('Uvicorn running')) {
          mainWindow.webContents.send('backend:ready');
        }
      });

      pythonProcess.stderr.on('data', (data) => {
        console.error(`Python stderr: ${data}`);
      });

      pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
      });

    } catch (error) {
      console.error('Failed to start backend:', error);
      dialog.showErrorBox('Backend Error', 'Failed to start TerraSim backend server');
    }
  }

  setupIpcHandlers() {
    // File operations
    ipcMain.handle('file:read', async (event, filePath) => {
      try {
        const data = await fs.readFile(filePath, 'utf8');
        return { success: true, data };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('file:write', async (event, filePath, data) => {
      try {
        await fs.writeFile(filePath, data, 'utf8');
        return { success: true };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('file:exists', async (event, filePath) => {
      try {
        await fs.access(filePath);
        return true;
      } catch {
        return false;
      }
    });

    // API proxy
    ipcMain.handle('api:request', async (event, method, url, data) => {
      try {
        const config = {
          method: method.toLowerCase(),
          url: `http://localhost:8000${url}`,
          timeout: 30000
        };

        if (data && ['post', 'put', 'patch'].includes(method.toLowerCase())) {
          config.data = data;
          config.headers = { 'Content-Type': 'application/json' };
        }

        const response = await axios(config);
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // System info
    ipcMain.handle('system:get-info', () => {
      return {
        platform: process.platform,
        arch: process.arch,
        nodeVersion: process.version,
        electronVersion: process.versions.electron,
        appVersion: app.getVersion()
      };
    });

    // Dialog operations
    ipcMain.handle('dialog:show-save', async (event, options) => {
      const result = await dialog.showSaveDialog(mainWindow, options);
      return result;
    });

    ipcMain.handle('dialog:show-open', async (event, options) => {
      const result = await dialog.showOpenDialog(mainWindow, options);
      return result;
    });

    ipcMain.handle('dialog:show-message', async (event, options) => {
      const result = await dialog.showMessageBox(mainWindow, options);
      return result;
    });

    // Window operations
    ipcMain.handle('window:minimize', () => {
      if (mainWindow) mainWindow.minimize();
    });

    ipcMain.handle('window:maximize', () => {
      if (mainWindow) {
        if (mainWindow.isMaximized()) {
          mainWindow.unmaximize();
        } else {
          mainWindow.maximize();
        }
      }
    });

    ipcMain.handle('window:close', () => {
      if (mainWindow) mainWindow.close();
    });
  }

  cleanup() {
    // Cleanup Python process
    if (pythonProcess) {
      pythonProcess.kill();
      pythonProcess = null;
    }

    // Cleanup server process
    if (serverProcess) {
      serverProcess.kill();
      serverProcess = null;
    }
  }
}

// Initialize the application
new TerraSimElectron();
