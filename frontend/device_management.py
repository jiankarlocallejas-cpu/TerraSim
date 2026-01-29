"""
Device Management Screen
Show trusted devices, login history, and manage access
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List, Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class DeviceManagementScreen(ttk.Frame):
    """Screen for managing trusted devices and viewing login history"""
    
    def __init__(self, parent, user_id: int, device_manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.user_id = user_id
        self.device_manager = device_manager
        self.selected_device = None
        
        self._create_widgets()
        self.refresh_data()
    
    def _create_widgets(self):
        """Create UI components"""
        # Title
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        title_label = ttk.Label(
            title_frame,
            text="Trusted Devices & Login History",
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        refresh_btn = ttk.Button(
            title_frame,
            text="↻ Refresh",
            command=self.refresh_data
        )
        refresh_btn.pack(side=tk.RIGHT)
        
        # Main content
        content = ttk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Devices section
        devices_frame = ttk.LabelFrame(content, text="Active Devices", padding=10)
        devices_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Devices treeview
        tree_cols = ("Device", "OS", "Last Login", "Status")
        self.devices_tree = ttk.Treeview(devices_frame, columns=tree_cols, height=6, show="headings")
        
        self.devices_tree.column("Device", width=200)
        self.devices_tree.column("OS", width=100)
        self.devices_tree.column("Last Login", width=180)
        self.devices_tree.column("Status", width=100)
        
        for col in tree_cols:
            self.devices_tree.heading(col, text=col)
        
        self.devices_tree.pack(fill=tk.BOTH, expand=True)
        self.devices_tree.bind("<<TreeviewSelect>>", self._on_device_select)
        
        # Device actions
        device_actions = ttk.Frame(devices_frame)
        device_actions.pack(fill=tk.X, pady=(10, 0))
        
        self.trust_btn = ttk.Button(
            device_actions,
            text="[OK] Trust Device",
            command=self.trust_selected_device,
            state=tk.DISABLED
        )
        self.trust_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.revoke_btn = ttk.Button(
            device_actions,
            text="✕ Revoke Access",
            command=self.revoke_selected_device,
            state=tk.DISABLED,
            foreground="red"
        )
        self.revoke_btn.pack(side=tk.LEFT)
        
        # Login history section
        history_frame = ttk.LabelFrame(content, text="Login History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        # History treeview
        history_cols = ("Time", "Device", "Event", "Status", "IP Address")
        self.history_tree = ttk.Treeview(history_frame, columns=history_cols, height=8, show="headings")
        
        self.history_tree.column("Time", width=150)
        self.history_tree.column("Device", width=150)
        self.history_tree.column("Event", width=80)
        self.history_tree.column("Status", width=80)
        self.history_tree.column("IP Address", width=120)
        
        for col in history_cols:
            self.history_tree.heading(col, text=col)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for history
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
    
    def refresh_data(self):
        """Refresh devices and history from database"""
        if not self.device_manager:
            return
        
        # Clear existing data
        for item in self.devices_tree.get_children():
            self.devices_tree.delete(item)
        
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Load devices
        try:
            devices = self.device_manager.get_user_devices(self.user_id)
            for device in devices:
                last_login = device.get('last_login')
                if last_login:
                    try:
                        dt = datetime.fromisoformat(last_login)
                        last_login = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                status = "Trusted ✓" if device.get('is_trusted') else "Untrusted"
                self.devices_tree.insert(
                    "",
                    tk.END,
                    values=(
                        device.get('device_name', 'Unknown'),
                        device.get('os', 'Unknown'),
                        last_login or "Never",
                        status
                    ),
                    tags=(device.get('id'),)
                )
        except Exception as e:
            logger.error(f"Failed to load devices: {e}")
        
        # Load login history
        try:
            history = self.device_manager.get_login_history(self.user_id, limit=50)
            for event in history:
                created_at = event.get('created_at')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at)
                        created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                
                status = "Success ✓" if event.get('success') else "Failed ✕"
                ip = event.get('ip_address', 'Unknown')
                
                self.history_tree.insert(
                    "",
                    tk.END,
                    values=(
                        created_at or "Unknown",
                        event.get('device_name', 'Unknown'),
                        event.get('event_type', 'Unknown'),
                        status,
                        ip
                    )
                )
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
    
    def _on_device_select(self, event):
        """Handle device selection"""
        selection = self.devices_tree.selection()
        if selection:
            item = selection[0]
            self.selected_device = item
            self.trust_btn.config(state=tk.NORMAL)
            self.revoke_btn.config(state=tk.NORMAL)
        else:
            self.selected_device = None
            self.trust_btn.config(state=tk.DISABLED)
            self.revoke_btn.config(state=tk.DISABLED)
    
    def trust_selected_device(self):
        """Mark selected device as trusted"""
        if not self.selected_device or not self.device_manager:
            messagebox.showwarning("No Selection", "Please select a device first")
            return
        
        try:
            # Get device ID from tags
            item = self.devices_tree.item(self.selected_device)
            device_name = item['values'][0]
            
            if self.device_manager.trust_device(self.user_id, int(self.selected_device)):
                messagebox.showinfo("Success", f"Device '{device_name}' is now trusted")
                self.refresh_data()
            else:
                messagebox.showerror("Error", "Failed to trust device")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
    
    def revoke_selected_device(self):
        """Revoke access for selected device"""
        if not self.selected_device or not self.device_manager:
            messagebox.showwarning("No Selection", "Please select a device first")
            return
        
        item = self.devices_tree.item(self.selected_device)
        device_name = item['values'][0]
        
        if messagebox.askyesno(
            "Confirm Revoke",
            f"Are you sure you want to revoke access for '{device_name}'?\nYou won't be able to login from this device."
        ):
            try:
                if self.device_manager.revoke_device(self.user_id, int(self.selected_device)):
                    messagebox.showinfo("Success", f"Device '{device_name}' access revoked")
                    self.refresh_data()
                else:
                    messagebox.showerror("Error", "Failed to revoke device")
            except Exception as e:
                messagebox.showerror("Error", f"Error: {str(e)}")


def create_device_management_window(user_id: int, device_manager) -> tk.Tk:
    """Create standalone device management window"""
    root = tk.Tk()
    root.title("TerraSim - Device Management")
    root.geometry("900x600")
    
    # Configure style
    style = ttk.Style()
    style.theme_use('clam')
    
    screen = DeviceManagementScreen(root, user_id, device_manager)
    screen.pack(fill=tk.BOTH, expand=True)
    
    return root


if __name__ == "__main__":
    # Demo
    root = tk.Tk()
    root.title("Device Management Demo")
    root.geometry("900x600")
    
    screen = DeviceManagementScreen(root, user_id=1, device_manager=None)
    screen.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()
