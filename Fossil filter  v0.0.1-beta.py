#---shitcode---

from tkinter import ttk, filedialog, messagebox, filedialog, Listbox, SINGLE, MULTIPLE
import tkinter as tk
import pandas as pd
import numpy as np
import functools
import re

class SpFilterWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(" 未定名筛选 ")
        self.geometry("700x700")
        self.df = master.df
        self.list = ['sp','cf','nov','aff']
        self.sign_list = ['?']

        if self.df.shape[1] < 2:
            messagebox.showerror("错误", "请检查csv文件")
            self.destroy()
            return
        
        self.Label_SpFilter = tk.Label(self, text="选择需要去除的未定名")
        self.Label_SpFilter.pack(pady=10)

        self.unique_listbox = Listbox(self)
        self.unique_listbox.pack(pady=17, fill="x")

        self.check_vars = [tk.IntVar() for _ in range(len(self.list))]
        self.check_vars_1 = [tk.IntVar() for _ in range(len(self.sign_list))]

        # 创建复选框
        for i, option in enumerate(self.list):
            tk.Checkbutton(self, text=option, variable=self.check_vars[i]).pack(side='left', anchor='nw', fill='x')

        for j, option1 in enumerate(self.sign_list):
            tk.Checkbutton(self, text=option1, variable=self.check_vars_1[j]).pack(side='left', anchor='nw', fill='x')        

        self.apply_button1 = tk.Button(self, text="应用筛选", command=self.get_checked_items)
        self.apply_button1.pack(pady=5)

        unique_values = self.df.iloc[1:,1].unique()
        self.unique_listbox.delete(0, tk.END)

        for value in unique_values:
            if pd.notna(value):#过滤NaN
                self.unique_listbox.insert(tk.END, value)

    def get_checked_items(self):
        self.selected_items = [self.list[i] for i in range(len(self.list)) if self.check_vars[i].get()]
        self.selected_items_sign = [self.sign_list[j] for j in range(len(self.sign_list)) if self.check_vars_1[j].get()]
        self.sp_filter()

    def sp_filter(self):
        filters=[]
        for string in self.selected_items:  
            filter = self.df.iloc[1:,1].astype(str).str.contains(fr'\b{re.escape(string)}')
            filters.append(filter)

        for sign in self.selected_items_sign:  
            filter = self.df.iloc[1:,1].astype(str).str.contains(fr'{re.escape(sign)}')
            filters.append(filter)        

        result = ~functools.reduce(lambda x, y: x | y, filters) #取或非
        new_result = np.concatenate(([True], result.values))
        self.master.df = self.df[new_result]
        messagebox.showinfo("完成", "完成")
        self.destroy()
        # print(self.master.df)
        # print(result)

class FossilGroupFilterWindow(tk.Toplevel):
    """
    FossilGroup 筛选
    """
    def __init__(self, master):
        super().__init__(master)
        self.title("FossilGroup 筛选")
        self.geometry("700x500")
        self.df = master.df

        self.Label_FossilGroup = tk.Label(self, text="选择需要保留的物种")
        self.Label_FossilGroup.pack(pady=10)

        self.unique_listbox = Listbox(self, selectmode=MULTIPLE, height=17)
        self.unique_listbox.pack(pady=10, fill="x")

        self.show_unique_values()

        self.export_button = tk.Button(self, text="确定", command=self.select)
        self.export_button.pack(pady=10)

    def select(self):
        try:
            self.selected_values = [self.unique_listbox.get(i) for i in self.unique_listbox.curselection()]
            mask = self.df["FossilGroup"].isin(self.selected_values)
            mask.iloc[0] = True  # 保证第0行始终为 True
            self.master.df = self.df[mask]
            messagebox.showinfo("完成", "完成")
            self.destroy()

        except IndexError:
            messagebox.showerror("错误", "未知错误")
    
    def show_unique_values(self):
        try:
            column_name = "FossilGroup"
            unique_values = self.df[column_name].unique()
            unique_values = sorted([x for x in unique_values if not (isinstance(x, float) and np.isnan(x))])
            # print(unique_values)
            self.unique_listbox.delete(0, tk.END)

            for value in unique_values:
                #过滤NaN
                if pd.notna(value):
                    self.unique_listbox.insert(tk.END, value)
        except IndexError:
            messagebox.showerror("错误", "无物种信息列")

class NonEmptyCellFilterWindow(tk.Toplevel):
    """
    按行列筛选非空单元格
    """
    def __init__(self, master):
        super().__init__(master)
        self.title("非空单元格筛选")
        self.geometry("400x100")#("800x500")
        self.df = master.df

        #--------------------------一坨屎--------------------------
        pd.options.mode.copy_on_write = True
        self.df.loc[-1] = self.df.columns  # 将列名作为新的一行（索引设为 -1）
        self.df.index = self.df.index + 1   # 重新排序索引，使新行成为第一行
        self.df = self.df.sort_index()      # 按索引排序，确保新行在第一行
        self.df.columns = range(self.df.shape[1])  # 重置列名为默认整数索引
        #----------------防止列名中nan重复拉了一坨------------------

        self.threshold_frame = tk.Frame(self)
        self.threshold_frame.pack(pady=5)
        tk.Label(self.threshold_frame, text="最小物种数:").pack(side="left")
        self.threshold_col = tk.Entry(self.threshold_frame, width=10)
        self.threshold_col.pack(side="left", padx=5)

        tk.Label(self.threshold_frame, text="最小剖面数:").pack(side="left")
        self.threshold_row = tk.Entry(self.threshold_frame, width=10)
        self.threshold_row.pack(side="left", padx=5)

        # 应用筛选按钮
        self.apply_button = tk.Button(self, text="应用筛选", command=self.iterative_filter)
        self.apply_button.pack(pady=5)

    def iterative_filter(self):
        self.col_min = int(self.threshold_col.get())
        self.row_min = int(self.threshold_row.get())

        try:
            self.df = self.df
            while True:
                prev_shape = self.df.shape
                
                #列
                invalid_cols = self.df.columns[self.df.iloc[2:, :].notna().sum() < self.col_min]
                invalid_cols = invalid_cols[0:-2] #保留Note和TaxonMixedID前的一空列
                self.df = self.df.drop(invalid_cols, axis=1)
                
                #行
                invalid_rows = self.df.index[self.df.iloc[:, 2:-3].notna().sum(axis=1) < self.row_min*2]
                self.df = self.df.drop(invalid_rows, axis=0)

                # 如果本次迭代后形状不变，则退出循环
                if self.df.shape == prev_shape:
                    break
            self.df.columns = self.df.iloc[0]
            self.df = self.df.drop(0)            
            self.master.df = self.df
            messagebox.showinfo(title='筛选', message='完成')
            self.destroy()
        
        except IndexError:
            messagebox.showerror("错误", "请输入数字")

class MainApplication(tk.Tk):
    """
    主界面: CSV 加载与子界面管理
    """
    def __init__(self):
        super().__init__()
        self.title("筛选器")
        self.geometry("600x250")

        self.df = pd.DataFrame()

        self.load_button = tk.Button(self, text="加载 CSV 文件", command=self.load_csv)
        self.load_button.grid(row=0,column=0,padx=(10,0),pady=10)

        self.status_label = tk.Label(self, text="未加载 CSV 文件", fg="red")
        self.status_label.grid(row=2,column=0,padx=(10,0),pady=10)

        self.fossil_button = tk.Button(self, text="FossilGroup 筛选", command=self.open_fossil_filter, state="disabled")
        self.fossil_button.grid(row=0,column=2,padx=(10,0),pady=10)

        self.cfsp_button = tk.Button(self, text=" 未定名筛选 ", command=self.open_sp_filter, state="disabled")
        self.cfsp_button.grid(row=1,column=2,padx=(10,0),pady=10)

        self.nonempty_button = tk.Button(self, text="非空单元格筛选", command=self.open_nonempty_filter, state="disabled")
        self.nonempty_button.grid(row=2,column=2,padx=(10,0),pady=10)

        self.output_button = tk.Button(self, text="输出结果", command=self.output_csv, state="disabled")
        self.output_button.grid(row=3,column=2,padx=(10,0),pady=10)


    def combine_cols(self):  # 合并表头
        df = self.df
        for col in range(2, len(df.columns) - 5, 2):
            df.iloc[0, col] = f"{str(df.iloc[0, col]).strip()} {str(df.iloc[1, col]).strip()} {str(df.iloc[1, col+1]).strip()}"
        df.drop([1], axis=0, inplace=True)
        return df

    def load_csv(self):
        """
        在主界面加载 CSV 文件
        """
        self.file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if self.file_path:
            try:
                self.df = pd.read_csv(self.file_path, header=None)
                self.df = self.combine_cols()
                self.df.columns = self.df.iloc[0]
                self.df = self.df.drop(0)
                self.status_label.config(text=f"已加载文件: {self.file_path.split('/')[-1]}", fg="green")
                self.fossil_button.config(state="normal")
                self.nonempty_button.config(state="normal")
                self.cfsp_button.config(state="normal")
                self.output_button.config(state="normal")
            except Exception as e:
                messagebox.showerror("错误", f"加载 CSV 失败: {e}")

    def open_fossil_filter(self):
        """
        打开 FossilGroup 筛选子界面
        """
        if self.df.empty:
            messagebox.showerror("错误", "请先加载 CSV 文件")
            return
        FossilGroupFilterWindow(self)

    def open_nonempty_filter(self):
        """
        打开 非空单元格数量筛选子界面
        """
        if self.df.empty:
            messagebox.showerror("错误", "请先加载 CSV 文件")
            return
        NonEmptyCellFilterWindow(self)

    def open_sp_filter(self):
        """打开筛选 cf. / sp. 窗口"""
        if self.df.empty:
            messagebox.showerror("错误", "请先加载 CSV 文件")
            return
        SpFilterWindow(self)

    def output_csv(self):
        if self.df.empty:
            messagebox.showerror("错误", "请先加载 CSV 文件")
            return
        self.df.iloc[:, 0] = [np.nan] + list(range(1,self.df.shape[0]))
        output_path = self.file_path.split('/')[0:-1]
        output_path.append('清洗后.csv')
        path = "/".join(output_path)
        self.df.to_csv(path, index=None)#, header=None)
        messagebox.showinfo("完成", "输出至 清洗后.csv")

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()