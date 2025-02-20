
### 🏪 Shop Management System
-📌 Overview
The Shop Management System is a powerful, role-based inventory and sales tracking platform designed to help businesses manage shops, sales, inventory, and financial reports efficiently. Built with Django (backend) and TailwindCSS + Chart.js (frontend), the system ensures seamless user experience, dynamic analytics, and real-time tracking of sales, real-time notifications and stock movements.

### 🚀 Key Features
-🔹 User Roles & Access
-✅ Superadmin: Full system control, manages all users, shops, and reports.
-✅ Manager: Manages shops, sellers, inventory, and sales tracking.
-✅ Seller: Records sales, tracks stock, and manages credit payments.

### 🛒 Shop & Seller Management
-✅ Create & Manage Shops: Managers or Superadmins can create shops.
-✅ Assign Sellers to Shops: Sellers are linked to specific shops.
-✅ Inventory Management: Add, edit, delete products in the shop.
-✅ Low Stock Alerts: Get notified when stock is low.

### 💰 Sales & Credit Tracking
-✅ Record Sales: Sellers can record sales with multiple products.
-✅ Cash & Credit Sales: Choose between cash or credit transactions.
-✅ Partial Payments: Buyers can pay part of the amount and settle later.
-✅ Automatic Stock Reduction: Sold products reduce from inventory.
-✅ Sales History & Filtering: Search sales by date, seller, or shop.
-✅ Sales Returns: Delete or modify sales to return items to stock.

### 📊 Reports & Analytics
-✅ Sales Reports: Daily, Weekly, Monthly revenue breakdown.
-✅ Profit Analysis: Compare cost price vs selling price.
-✅ Top & Least Selling Products: Identify performance trends.
-✅ Credit Sales Report: Track outstanding customer payments.
-✅ Graphical Representations: Interactive charts using Chart.js.
-✅ Export Reports: Download reports as CSV or PDF.

### 🔔 Notifications & Alerts
-✅ Real-Time Low Stock Alerts: Get notified of products running out.
-✅ Pending Credit Payments Alert: Track customers with outstanding debts.
-✅ Sales & Performance Updates: Monitor daily sales trends.

### 🎨 User Interface & Experience
-✅ Django Admin Panel Style: Clean and professional UI.
-✅ Fixed Sidebar Navigation: Easy access to dashboard features.
-✅ Mobile Responsive: Works on all devices (PC, tablet, mobile).
-✅ Smooth UI with TailwindCSS: Fast-loading, modern design.
-✅ Interactive Graphs: Sales & profit trends using Chart.js.

### ⚙️ Tech Stack
-✅ Backend: Django (Python)
-✅ Frontend: HTML, TailwindCSS, JavaScript
-✅ Database: PostgreSQL / SQLite
-✅ Charts & Reports: Chart.js for analytics
-✅ Authentication: Django User Model



### 🔧 Installation & Setup
###  1️⃣ Clone the Repository
'''bash
Copy
Edit
git clone https://github.com/Pi-johns/shop-management-system.git
cd shop-management-system
### 2️⃣ Create a Virtual Environment & Install Dependencies
bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # For Linux/macOS
venv\Scripts\activate  # For Windows
pip install -r requirements.txt
### 3️⃣ Apply Migrations & Create Superuser
bash
Copy
Edit
python manage.py migrate
python manage.py createsuperuser
### 4️⃣ Run the Development Server
bash
Copy
Edit
python manage.py runserver
🔗 Open http://127.0.0.1:8000/ in your browser.

📜 License
This project is licensed under the MIT License.

🤝 Contributions & Support
Feel free to contribute to this project! Fork, modify, and submit a pull request.
For any issues, create a GitHub issue or contact the developer.

🔥 Built with ❤️ by Pi-johns! 🚀
