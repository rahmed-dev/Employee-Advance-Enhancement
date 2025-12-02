# Employee Advance Enhanced – User Guide

## Overview
Employee Advance Enhanced (app `eae`) adds a structured repayment schedule to the standard **Employee Advance** DocType and automates payroll deductions using **Additional Salary**.  
HR, Payroll, and Finance teams can configure one repayment plan per Employee Advance and let the system create deductions on each installment date.

## Prerequisites
- App `eae` is installed on your bench.
- Scheduler (background jobs) is running.
- You have access to:
  - **Salary Component**
  - **Employee Advance**
  - **Additional Salary** and payroll reports

---

## 1. Configure the repayment Salary Component (one-time)
1. Go to **HR > Payroll Setup > Salary Component**.
2. Create or open a **Deduction** Salary Component for advance repayment (for example, “Employee Advance Repayment”).
3. Check **Is Employee Advance Repayment Component**.
4. Click **Save**.

This component will be used for all automatic repayment deductions.

---

## 2. Create and submit an Employee Advance
Use the standard Employee Advance DocType.

1. Go to **HR > Employee > Employee Advance > New**.
2. Select **Employee** and enter the **Advance Amount** and other required fields.
3. Click **Save**, then **Submit** the Employee Advance.
4. Disburse the advance as you normally do so that **Paid Amount (`paid_amount`)** is updated.

---

## 3. Create a repayment schedule from Employee Advance
1. Open the **submitted Employee Advance**.
2. Click the **Repayment Schedule** tab.
3. Click **Create Repayment Schedule**.
4. In the dialog, fill:
   - **Schedule Type**:  
     - *Fixed Number of Installments* **or**  
     - *Fixed Installment Amount*
   - **Repayment Frequency**: Monthly / Semi-monthly / Every 3 Months
   - **Start Date**
   - **Repayment Salary Component**: choose the component you flagged earlier.
5. Click **Preview Schedule** to review the installment dates and amounts.
6. If everything looks correct, click **Create Schedule**.

The **Repayment Schedule** tab will now show:
- Remaining advance balance
- Total / paid / remaining installments
- A table of installments with date, amount, and status

---

## 4. Run payroll with automatic repayments
Once a schedule is active, repayments are handled through **Additional Salary** entries.

1. On or after each **Installment Date**, the system creates a **non-recurring Additional Salary** for the employee:
   - Type: **Deduction**
   - **Payroll Date** = Installment Date
   - Linked to the **Employee Advance**
2. When you generate **Salary Slips** (or use **Payroll Entry**), these deduction rows are included automatically.
3. When Additional Salary documents are submitted, **Return Amount (`return_amount`)** on the Employee Advance increases and the remaining balance decreases.

You do not need to create these repayment deductions manually.

---

## 5. Monitor remaining balance and schedule status
To review a specific advance:

1. Open the **Employee Advance**.
2. Go to the **Repayment Schedule** tab.
3. Check:
   - **Remaining Balance** (Paid Amount – Return Amount)
   - **Schedule Status** (Draft, Active, Closed, etc.)
   - **Installments Table** with status (Planned, Paid, Skipped) and links to Additional Salary.

You can also open the **Employee Advance Repayment Schedule** DocType to see all schedules and their installments in one place.

---

## 6. Handle early payoff or termination
If an employee repays the remaining balance early (for example, via a Payment Entry or Journal Entry):

1. Post the repayment so that **Return Amount (`return_amount`)** equals the **Paid Amount (`paid_amount`)** on the Employee Advance.
2. When the remaining balance reaches zero:
   - The **Employee Advance** is marked fully settled using standard HRMS behavior.
   - The linked **Repayment Schedule** is set to **Closed**.
   - Any future **Planned** installments without Additional Salary are marked **Skipped**.

No further automatic repayment deductions will be created after the schedule is closed.

---

## 7. What employees see
- Employees can open their own **Employee Advance** records from the Desk (based on your permissions setup).
- On the **Repayment Schedule** tab they can:
  - View their remaining balance
  - See upcoming installment dates and amounts
  - See which installments are already paid
- The schedule is **read-only** for employees; only HR/Payroll/Finance users can create or update schedules.
