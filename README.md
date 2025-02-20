
### 🏪 Shop Management System
-📌 Overview
The Shop Management System is a powerful, role-based inventory and sales tracking platform designed to help businesses manage shops, sales, inventory, and financial reports efficiently. Built with Django (backend) and TailwindCSS + Chart.js (frontend), the system ensures seamless user experience, dynamic analytics, and real-time tracking of sales, real-time notifications and stock movements.

### 🚀 Key Features
- 🔹 User Roles & Access
- ✅ Superadmin: Full system control, manages all users, shops, and reports.
- ✅ Manager: Manages shops, sellers, inventory, and sales tracking.
- ✅ Seller: Records sales, tracks stock, and manages credit payments.

### 🛒 Shop & Seller Management
- ✅ Create & Manage Shops: Managers or Superadmins can create shops.
- ✅ Assign Sellers to Shops: Sellers are linked to specific shops.
- ✅ Inventory Management: Add, edit, delete products in the shop.
- ✅ Low Stock Alerts: Get notified when stock is low.

### 💰 Sales & Credit Tracking
- ✅ Record Sales: Sellers can record sales with multiple products.
- ✅ Cash & Credit Sales: Choose between cash or credit transactions.
- ✅ Partial Payments: Buyers can pay part of the amount and settle later.
- ✅ Automatic Stock Reduction: Sold products reduce from inventory.
- ✅ Sales History & Filtering: Search sales by date, seller, or shop.
- ✅ Sales Returns: Delete or modify sales to return items to stock.

### 📊 Reports & Analytics
- ✅ Sales Reports: Daily, Weekly, Monthly revenue breakdown.
- ✅ Profit Analysis: Compare cost price vs selling price.
- ✅ Top & Least Selling Products: Identify performance trends.
- ✅ Credit Sales Report: Track outstanding customer payments.
- ✅ Graphical Representations: Interactive charts using Chart.js.
- ✅ Export Reports: Download reports as CSV or PDF.

### 🔔 Notifications & Alerts
- ✅ Real-Time Low Stock Alerts: Get notified of products running out.
- ✅ Pending Credit Payments Alert: Track customers with outstanding debts.
- ✅ Sales & Performance Updates: Monitor daily sales trends.

### 🎨 User Interface & Experience
- ✅ Django Admin Panel Style: Clean and professional UI.
- ✅ Fixed Sidebar Navigation: Easy access to dashboard features.
- ✅ Mobile Responsive: Works on all devices (PC, tablet, mobile).
- ✅ Smooth UI with TailwindCSS: Fast-loading, modern design.
- ✅ Interactive Graphs: Sales & profit trends using Chart.js.

### ⚙️ Tech Stack
- ✅ Backend: Django (Python)
- ✅ Frontend: HTML, TailwindCSS, JavaScript
- ✅ Database: PostgreSQL / SQLite
- ✅ Charts & Reports: Chart.js for analytics
- ✅ Authentication: Django User Model

## 📸 Screenshots  🪄✨

### 🔥 Home Page for login
![Home Page](static/images/![Screenshot from 2025-02-20 03-15-40](https://github.com/user-attachments/assets/310c296f-f8e7-451b-895b-62868970ded1)
)

### 📜 manager dashboard
![Projects Page](static/images/![Screenshot from 2025-02-20 03-18-58](https://github.com/user-attachments/assets/97fc7a69-2720-4c7e-b6c2-a03c1bc82205)
)

### ✨ reports
![Contact Page](static/images/![Screenshot from 2025-02-20 03-19-45](https://github.com/user-attachments/assets/1cb3d05b-ced2-43dd-a6b3-49e4fb49f858)
)

### ✨ reports
![Contact Page](static/images/![Screenshot from 2025-02-20 03-20-15](https://github.com/user-attachments/assets/6f112588-15fe-4dca-8eb1-1aeab5e0b212)
)

### ✨ admin dash
![Contact Page](static/images/![Screenshot from 2025-02-20 03-21-31](https://github.com/user-attachments/assets/093265e4-38d3-4079-bc8a-ad9c40c723ba)
)

### ✨ admin dash inventory management
![Contact Page](static/images/![Screenshot from 2025-02-20 03-22-40](https://github.com/user-attachments/assets/1700c9de-d333-46ab-adb9-989e9399da31)
)

### ✨ admin dash sales management
![Contact Page](static/images/![Screenshot from 2025-02-20 03-23-57](https://github.com/user-attachments/assets/c594ee09-b114-4995-9ad4-887c9435b723)


### ✨ django admin panel
![Contact Page](static/images/![Screenshot from 2025-02-20 03-26-29](https://github.com/user-attachments/assets/7f6daced-030b-4aa3-a355-bcb3751baa28)
)

### ✨ users and roles
![Contact Page](static/images/![Screenshot from 2025-02-20 03-27-12](https://github.com/user-attachments/assets/e32445c3-f3f6-41df-aa09-864c2f51fc63)
)

### ✨ modify user
![Contact Page](static/images/![Screenshot from 2025-02-20 03-27-46](https://github.com/user-attachments/assets/f7e91b32-dfd3-47ef-b8a8-7936fbdcc444)
)

---


### 🔧 Installation & Setup

## 📜 **How to Install & Run Locally**

```bash
# Clone the repository
git clone https://github.com/your-repo/shop-management.git
cd shop-management

# Create a virtual environment and activate it
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Start the server
python manage.py runserver


```

Now, visit **http://127.0.0.1:8000/** and log in! 🚀  

---

## 🎯 **User Roles & Actions**

| Role         | Actions |
|-------------|--------------------------------|
| Superadmin  | Manage all users, shops, reports, notifications |
| Manager     | Manage inventory, sellers, sales tracking |
| Seller      | Record sales, manage payments, view reports |

---

## 📌 **Future Enhancements**
- 🔄 **AI-based Sales Predictions**
- 📱 **Mobile App Integration**
- 🏆 **Loyalty Program for Customers**

---

## 💡 **Contributors**
Developed by **Pi-Johns** 🚀  

🤝 Contributions & Support
Feel free to contribute to this project! Fork, modify, and submit a pull request.
For any issues, create a GitHub issue or contact the developer.


