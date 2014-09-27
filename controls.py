import Tkinter
tk = Tkinter
class MyWindow(tk.Frame):
    def leaveit(self):
        sys.exit()
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        label = tk.Label(root, text="Hello, world")
        button1 = tk.Button(label,text="hi there", command=self.quit())
        button1.pack()
        label.pack()
        label.bind("<1>", self.quit)

root = tk.Tk()
MyWindow(root).pack()
root.mainloop()