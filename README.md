# Leather Workshop Management System

A comprehensive inventory and project management system designed specifically for leather workshops, enabling efficient tracking of materials, recipes, parts, and production processes.

## 1. Project Overview

The Store Management System is a specialized software solution for leather workshops, providing comprehensive tools to manage inventory, track recipes (project part lists), handle orders, and manage suppliers. It offers a user-friendly interface with robust data management capabilities, helping artisans and workshop managers optimize their workflow and maintain precise inventory control.

## 2. Features

- 📦 Detailed Inventory Management
  - Track materials, parts, and leather inventory
  - Real-time stock level monitoring
  - Low stock alerts

- 🧾 Recipe (Project) Tracking
  - Create and manage detailed project recipes
  - Track materials used in each project
  - Comprehensive material and part listings

- 🚚 Supplier Management
  - Complete supplier database
  - Order tracking
  - Supplier performance monitoring

- 📊 Advanced Reporting
  - Inventory reports
  - Order analysis
  - Supplier performance insights

- 🔄 Comprehensive Operations
  - Undo/Redo functionality
  - Search and filter capabilities
  - Batch operations
  - Data import/export

## 3. Installation

### 3.1 Prerequisites

- Python 3.8+
- pip package manager
- Recommended: Virtual environment

### 3.2 Setup Instructions

```bash
# Clone the repository
git clone https://github.com/yourusername/leather-workshop-management.git
cd leather-workshop-management

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Initialize database
python database/database_setup.py

# Run the application
python main.py
```


## 4. Modules

### 4.1 Product Management
- **Storage View**: Track and manage product inventory  
- **Recipe View**: Create and manage project recipes  

### 4.2 Storage Management
- **Shelf Management**: Track leather and material storage  
- **Sorting System**: Organize and track parts and materials  

### 4.3 Order Management
- **Incoming Goods**: Track and process incoming materials  
- **Shopping Lists**: Manage procurement needs  
- **Supplier Management**: Track and manage supplier information  

---

## 5. Data Management

### 5.1 Data Validation
- Comprehensive input validation  
- Type and constraint checking  
- Automated error detection and reporting  

### 5.2 Backup System
- Automatic database backups  
- Manual export and import functionality  
- Backup version management  

---

## 6. Security Features
- Robust error handling  
- Logging of all critical operations  
- Data integrity checks  

---

## 7. Technology Stack
- 🐍 **Python 3.8+**  
- 🗃️ **SQLite Database**  
- 🖥️ **Tkinter GUI**  
- 📊 **Pandas** for data manipulation  
- 🔍 **SQLAlchemy** (future consideration)  

---

## 8. Roadmap
- User authentication system  
- Advanced reporting and analytics  
  

---

## 9. Contributing

Fork the repository
Create a feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request

## 10. License
Distributed under the MIT License. See LICENSE for more information.
## 11. Contact
Bernard Pas - PasBernard@protonmail.com
Project Link: https://github.com/yourusername/leather-workshop-management