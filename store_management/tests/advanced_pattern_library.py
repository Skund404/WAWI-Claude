

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class AdvancedPatternLibrary(tk.Frame):

        @inject(MaterialService)
        def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()

        @inject(MaterialService)
        def setup_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.pattern_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.pattern_frame, text='Pattern Library')
        self.test_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.test_frame, text='Tests')
        self.setup_pattern_library()
        self.setup_test_suite()

        @inject(MaterialService)
        def setup_pattern_library(self):
        ttk.Label(self.pattern_frame, text='Pattern Library Placeholder').pack(
            pady=20)

        @inject(MaterialService)
        def setup_test_suite(self):
        self.test_output = tk.Text(self.test_frame, wrap=tk.WORD)
        self.test_output.pack(fill=tk.BOTH, expand=True)
        self.run_tests_button = ttk.Button(self.test_frame, text=
            'Run Tests', command=self.run_tests)
        self.run_tests_button.pack(pady=10)

        @inject(MaterialService)
        def run_tests(self):
        self.test_output.delete('1.0', tk.END)
        suite = unittest.TestLoader().loadTestsFromTestCase(
            TestProjectWorkflowManager)
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)
        self.test_output.insert(tk.END, stream.getvalue())
        summary = f'\n\nTest Summary:\n'
        summary += f'Ran {result.testsRun} tests\n'
        summary += (
            f'Successes: {result.testsRun - len(result.failures) - len(result.errors)}\n'
            )
        summary += f'Failures: {len(result.failures)}\n'
        summary += f'Errors: {len(result.errors)}\n'
        self.test_output.insert(tk.END, summary)


if __name__ == '__main__':
    root = tk.Tk()
    app = AdvancedPatternLibrary(root)
    app.pack(fill='both', expand=True)
    root.mainloop()
