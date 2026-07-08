import json
import csv
import shutil
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk


DATA_FILE = Path("finance_data.json")
DEFAULT_CATEGORIES = [
    "Food",
    "Travel",
    "Rent",
    "Entertainment",
    "Bills",
    "Shopping",
    "Health",
    "Education",
    "Other",
]


def load_data():
    if DATA_FILE.exists():
        try:
            with DATA_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}

    transactions = data.get("transactions", [])
    budget = float(data.get("budget", 0.0))
    categories = data.get("categories", DEFAULT_CATEGORIES[:]) or DEFAULT_CATEGORIES[:]

    return {
        "transactions": transactions,
        "budget": budget,
        "categories": categories,
    }


def save_data(data):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def calculate_totals(data):
    total_income = sum(
        item["amount"] for item in data["transactions"] if item["type"] == "income"
    )
    total_expenses = sum(
        item["amount"] for item in data["transactions"] if item["type"] == "expense"
    )
    return total_income, total_expenses, total_income - total_expenses


class FinanceTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance and Expenses Tracker")
        self.root.geometry("1050x650")
        self.root.minsize(950, 600)

        self.data = load_data()

        self.type_var = tk.StringVar(value="expense")
        self.amount_var = tk.StringVar()
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.category_var = tk.StringVar(value=self.data["categories"][0])
        self.note_var = tk.StringVar()
        self.month_var = tk.StringVar(value=datetime.now().strftime("%Y-%m"))
        self.budget_var = tk.StringVar(value=f"{self.data['budget']:.2f}")

        self.income_value = tk.StringVar()
        self.expense_value = tk.StringVar()
        self.balance_value = tk.StringVar()
        self.budget_value = tk.StringVar()
        self.monthly_text = tk.StringVar()

        self._configure_style()
        self._build_layout()
        self.refresh_ui()

    def _configure_style(self):
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

        self.root.configure(bg="#f4f6fb")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), background="#f4f6fb")
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10), foreground="#5b6577", background="#f4f6fb")
        style.configure("CardTitle.TLabel", font=("Segoe UI", 10, "bold"), background="#ffffff", foreground="#4c5666")
        style.configure("CardValue.TLabel", font=("Segoe UI", 16, "bold"), background="#ffffff", foreground="#1c2431")
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_layout(self):
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(2, weight=1)

        header = ttk.Frame(container)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        ttk.Label(header, text="Personal Finance Tracker", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Track income, expenses, savings, budget, and monthly spending in one window.",
            style="SubHeader.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        summary = ttk.Frame(container)
        summary.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        for index in range(4):
            summary.columnconfigure(index, weight=1)

        self._create_summary_card(summary, 0, "Total Income", self.income_value)
        self._create_summary_card(summary, 1, "Total Expenses", self.expense_value)
        self._create_summary_card(summary, 2, "Balance", self.balance_value)
        self._create_summary_card(summary, 3, "Budget Left", self.budget_value)

        form_card = ttk.Frame(container, style="Card.TFrame", padding=16)
        form_card.grid(row=2, column=0, sticky="nsw", padx=(0, 14))

        ttk.Label(form_card, text="Add Transaction", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        ttk.Label(form_card, text="Type").grid(row=1, column=0, sticky="w", pady=6)
        type_box = ttk.Combobox(
            form_card,
            textvariable=self.type_var,
            values=["income", "expense"],
            state="readonly",
            width=18,
        )
        type_box.grid(row=1, column=1, sticky="ew", pady=6)
        type_box.bind("<<ComboboxSelected>>", lambda event: self._update_category_state())

        ttk.Label(form_card, text="Amount").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(form_card, textvariable=self.amount_var, width=20).grid(
            row=2, column=1, sticky="ew", pady=6
        )

        ttk.Label(form_card, text="Date").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(form_card, textvariable=self.date_var, width=20).grid(
            row=3, column=1, sticky="ew", pady=6
        )

        ttk.Label(form_card, text="Category").grid(row=4, column=0, sticky="w", pady=6)
        self.category_box = ttk.Combobox(
            form_card,
            textvariable=self.category_var,
            values=self.data["categories"],
            width=18,
        )
        self.category_box.grid(row=4, column=1, sticky="ew", pady=6)

        ttk.Label(form_card, text="Note").grid(row=5, column=0, sticky="w", pady=6)
        ttk.Entry(form_card, textvariable=self.note_var, width=20).grid(
            row=5, column=1, sticky="ew", pady=6
        )

        ttk.Button(form_card, text="Save Transaction", command=self.add_transaction).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(12, 8)
        )
        ttk.Button(form_card, text="Delete Selected", command=self.delete_selected).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=4
        )
        ttk.Button(form_card, text="Set Budget", command=self.set_budget).grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=4
        )
        ttk.Button(form_card, text="Show Monthly Summary", command=self.show_monthly_summary).grid(
            row=9, column=0, columnspan=2, sticky="ew", pady=4
        )
        ttk.Button(form_card, text="Export CSV Report", command=self.export_csv_report).grid(
            row=10, column=0, columnspan=2, sticky="ew", pady=4
        )
        ttk.Button(form_card, text="Backup Data", command=self.backup_data).grid(
            row=11, column=0, columnspan=2, sticky="ew", pady=4
        )
        ttk.Button(form_card, text="Restore Backup", command=self.restore_data).grid(
            row=12, column=0, columnspan=2, sticky="ew", pady=4
        )
        ttk.Button(form_card, text="Clear Form", command=self.clear_form).grid(
            row=13, column=0, columnspan=2, sticky="ew", pady=4
        )

        ttk.Label(form_card, text="Summary Month").grid(row=14, column=0, sticky="w", pady=(16, 6))
        ttk.Entry(form_card, textvariable=self.month_var, width=20).grid(
            row=14, column=1, sticky="ew", pady=(16, 6)
        )

        table_card = ttk.Frame(container, style="Card.TFrame", padding=16)
        table_card.grid(row=2, column=1, sticky="nsew")
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(1, weight=1)

        ttk.Label(table_card, text="Transactions", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        columns = ("date", "type", "category", "amount", "note")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("date", text="Date")
        self.tree.heading("type", text="Type")
        self.tree.heading("category", text="Category")
        self.tree.heading("amount", text="Amount")
        self.tree.heading("note", text="Note")
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("type", width=90, anchor="center")
        self.tree.column("category", width=130, anchor="center")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("note", width=240, anchor="w")
        self.tree.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        summary_box = ttk.LabelFrame(table_card, text="Monthly Analysis", padding=12)
        summary_box.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        summary_box.columnconfigure(0, weight=1)

        self.monthly_label = ttk.Label(
            summary_box,
            textvariable=self.monthly_text,
            justify="left",
            font=("Consolas", 10),
        )
        self.monthly_label.grid(row=0, column=0, sticky="w")

        self._update_category_state()

    def _create_summary_card(self, parent, column, title, value_var):
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 10, 0))
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=value_var, style="CardValue.TLabel").pack(anchor="w", pady=(6, 0))

    def _update_category_state(self):
        if self.type_var.get() == "income":
            self.category_var.set("Income")
            self.category_box.configure(state="disabled")
        else:
            if self.category_var.get() == "Income":
                self.category_var.set(self.data["categories"][0])
            self.category_box.configure(state="normal")

    def add_transaction(self):
        transaction_type = self.type_var.get()
        amount_text = self.amount_var.get().strip()
        date_text = self.date_var.get().strip()
        category = self.category_var.get().strip() or "Other"
        note = self.note_var.get().strip()

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount", "Enter a valid amount greater than 0.")
            return

        try:
            datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Use date format YYYY-MM-DD.")
            return

        if transaction_type == "expense" and category not in self.data["categories"]:
            self.data["categories"].append(category)
            self.category_box.configure(values=self.data["categories"])

        if transaction_type == "income":
            category = "Income"

        self.data["transactions"].append(
            {
                "type": transaction_type,
                "amount": amount,
                "date": date_text,
                "category": category,
                "note": note,
            }
        )
        save_data(self.data)
        self.refresh_ui()
        self.clear_form()
        messagebox.showinfo("Saved", "Transaction added successfully.")

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a transaction to delete.")
            return

        item_index = int(selected[0])
        transaction = self.data["transactions"][item_index]
        confirm = messagebox.askyesno(
            "Delete Transaction",
            f"Delete {transaction['category']} - {transaction['amount']:.2f}?",
        )
        if not confirm:
            return

        self.data["transactions"].pop(item_index)
        save_data(self.data)
        self.refresh_ui()

    def set_budget(self):
        budget_text = simpledialog.askstring(
            "Monthly Budget",
            "Enter your monthly budget:",
            initialvalue=self.budget_var.get().replace("Rs ", ""),
            parent=self.root,
        )
        if budget_text is None:
            return

        try:
            budget = float(budget_text)
            if budget < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Budget", "Enter a valid budget amount.")
            return

        self.data["budget"] = budget
        save_data(self.data)
        self.refresh_ui()
        messagebox.showinfo("Budget Saved", "Monthly budget updated successfully.")

    def show_monthly_summary(self):
        month = self.month_var.get().strip()
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            messagebox.showerror("Invalid Month", "Use month format YYYY-MM.")
            return

        monthly_transactions = [
            item for item in self.data["transactions"] if item["date"].startswith(month)
        ]
        if not monthly_transactions:
            self.monthly_text.set(f"No transactions found for {month}.")
            return

        income = sum(item["amount"] for item in monthly_transactions if item["type"] == "income")
        expenses = sum(
            item["amount"] for item in monthly_transactions if item["type"] == "expense"
        )

        category_totals = {}
        for item in monthly_transactions:
            if item["type"] == "expense":
                category_totals[item["category"]] = (
                    category_totals.get(item["category"], 0.0) + item["amount"]
                )

        lines = [
            f"Month: {month}",
            f"Income:   Rs {income:.2f}",
            f"Expenses: Rs {expenses:.2f}",
            f"Balance:  Rs {income - expenses:.2f}",
            "",
            "Category Breakdown:",
        ]

        if category_totals:
            for category, total in sorted(category_totals.items(), key=lambda item: item[1], reverse=True):
                lines.append(f"{category:<15} Rs {total:.2f}")
        else:
            lines.append("No expenses recorded.")

        self.monthly_text.set("\n".join(lines))

    def export_csv_report(self):
        if not self.data["transactions"]:
            messagebox.showwarning("No Data", "There are no transactions to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save CSV Report",
            defaultextension=".csv",
            initialfile="finance_report.csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not file_path:
            return

        with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Date", "Type", "Category", "Amount", "Note"])
            for item in sorted(self.data["transactions"], key=lambda transaction: transaction["date"]):
                writer.writerow(
                    [
                        item["date"],
                        item["type"].title(),
                        item["category"],
                        f"{item['amount']:.2f}",
                        item["note"],
                    ]
                )

        messagebox.showinfo("Export Complete", f"CSV report saved to:\n{file_path}")

    def backup_data(self):
        if not DATA_FILE.exists():
            save_data(self.data)

        file_path = filedialog.asksaveasfilename(
            title="Backup Finance Data",
            defaultextension=".json",
            initialfile=f"finance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            filetypes=[("JSON files", "*.json")],
        )
        if not file_path:
            return

        shutil.copyfile(DATA_FILE, file_path)
        messagebox.showinfo("Backup Complete", f"Backup saved to:\n{file_path}")

    def restore_data(self):
        file_path = filedialog.askopenfilename(
            title="Restore Backup",
            filetypes=[("JSON files", "*.json")],
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as backup_file:
                restored_data = json.load(backup_file)
        except (OSError, json.JSONDecodeError):
            messagebox.showerror("Restore Failed", "The selected backup file is invalid.")
            return

        self.data = {
            "transactions": restored_data.get("transactions", []),
            "budget": float(restored_data.get("budget", 0.0)),
            "categories": restored_data.get("categories", DEFAULT_CATEGORIES[:]) or DEFAULT_CATEGORIES[:],
        }
        save_data(self.data)
        self.category_var.set(self.data["categories"][0])
        self.refresh_ui()
        self.clear_form()
        messagebox.showinfo("Restore Complete", "Backup restored successfully.")

    def clear_form(self):
        self.amount_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.note_var.set("")
        self.type_var.set("expense")
        self.category_var.set(self.data["categories"][0])
        self._update_category_state()

    def refresh_ui(self):
        total_income, total_expenses, balance = calculate_totals(self.data)
        budget_left = self.data["budget"] - total_expenses if self.data["budget"] else 0.0

        self.income_value.set(f"Rs {total_income:.2f}")
        self.expense_value.set(f"Rs {total_expenses:.2f}")
        self.balance_value.set(f"Rs {balance:.2f}")
        if self.data["budget"] > 0:
            self.budget_value.set(f"Rs {budget_left:.2f}")
        else:
            self.budget_value.set("Not Set")

        self.budget_var.set(f"{self.data['budget']:.2f}")
        self.category_box.configure(values=self.data["categories"])

        for item in self.tree.get_children():
            self.tree.delete(item)

        sorted_transactions = sorted(
            enumerate(self.data["transactions"]),
            key=lambda item: item[1]["date"],
            reverse=True,
        )

        for original_index, transaction in sorted_transactions:
            self.tree.insert(
                "",
                "end",
                iid=str(original_index),
                values=(
                    transaction["date"],
                    transaction["type"].title(),
                    transaction["category"],
                    f"{transaction['amount']:.2f}",
                    transaction["note"],
                ),
            )

        self.show_monthly_summary()


def main():
    root = tk.Tk()
    FinanceTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
