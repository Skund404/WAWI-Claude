from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
logger = logging.getLogger(__name__)


class ProjectCostAnalyzer(BaseView):
    pass
"""
Analyze and track costs for leatherworking projects.
Provides detailed cost breakdowns, profitability analysis,
and pricing recommendations based on materials and labor.
"""

@inject(MaterialService)
def __init__(self, parent: tk.Widget, app: Any) -> None:
"""
Initialize the project cost analyzer.

Args:
parent: Parent widget
app: Application instance
"""
super().__init__(parent, app)
self.project_service = self.get_service(IProjectService)
self.material_service = self.get_service(IMaterialService)
self.error_handler = ErrorHandler()
self.current_project: Optional[Project] = None
self.cost_data: Dict[str, Decimal] = {}
self.labor_rate = Decimal('25.00')
self.setup_ui()
self.load_settings()

@inject(MaterialService)
def setup_ui(self) -> None:
"""Create and configure the UI components."""
self.toolbar = ttk.Frame(self)
self.toolbar.pack(fill=tk.X, padx=5, pady=5)
self.content = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
self.content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
self.create_toolbar()
self.create_project_section()
self.create_cost_section()
self.status_var = tk.StringVar()
ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN).pack(
fill=tk.X, pady=(5, 0))

@inject(MaterialService)
def create_toolbar(self) -> None:
"""Create toolbar controls."""
ttk.Label(self.toolbar, text='Project Type:').pack(side=tk.LEFT, padx=5
)
self.type_var = tk.StringVar(value='ALL')
type_combo = ttk.Combobox(self.toolbar, textvariable=self.type_var,
values=['ALL'] + [t.name for t in ProjectType], state='readonly', width=15)
type_combo.pack(side=tk.LEFT, padx=5)
type_combo.bind('<<ComboboxSelected>>', lambda _: self.load_projects())
ttk.Label(self.toolbar, text='Labor Rate ($/hr):').pack(side=tk.
LEFT, padx=5)
self.labor_var = tk.StringVar(value=str(self.labor_rate))
labor_entry = ttk.Entry(self.toolbar, textvariable=self.labor_var,
width=8)
labor_entry.pack(side=tk.LEFT)
labor_entry.bind('<FocusOut>', self.update_labor_rate)
ttk.Button(self.toolbar, text='Settings', command=self.
show_settings_dialog).pack(side=tk.RIGHT, padx=5)
ttk.Button(self.toolbar, text='Export Analysis', command=self.
export_analysis).pack(side=tk.RIGHT, padx=5)

@inject(MaterialService)
def create_project_section(self) -> None:
"""Create the project list section."""
frame = ttk.LabelFrame(self.content, text='Projects')
self.content.add(frame, weight=1)
columns = 'name', 'type', 'status', 'materials_cost', 'total_cost'
self.project_tree = ttk.Treeview(
frame, columns=columns, show='headings', height=15)
headings = {'name': 'Project Name', 'type': 'Type', 'status':
'Status', 'materials_cost': 'Materials Cost', 'total_cost':
'Total Cost'}
for col, heading in headings.items():
    pass
self.project_tree.heading(col, text=heading)
self.project_tree.column(col, width=100)
scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.
project_tree.yview)
self.project_tree.configure(yscrollcommand=scrollbar.set)
self.project_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
self.project_tree.bind('<<TreeviewSelect>>', self.on_project_select)

@inject(MaterialService)
def create_cost_section(self) -> None:
"""Create the cost analysis section."""
frame = ttk.LabelFrame(self.content, text='Cost Analysis')
self.content.add(frame, weight=1)
notebook = ttk.Notebook(frame)
notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
breakdown_frame = ttk.Frame(notebook)
notebook.add(breakdown_frame, text='Cost Breakdown')
self.create_cost_breakdown(breakdown_frame)
profit_frame = ttk.Frame(notebook)
notebook.add(profit_frame, text='Profitability')
self.create_profitability_analysis(profit_frame)
pricing_frame = ttk.Frame(notebook)
notebook.add(pricing_frame, text='Pricing')
self.create_pricing_recommendations(pricing_frame)

@inject(MaterialService)
def create_cost_breakdown(self, parent: ttk.Frame) -> None:
"""
Create the cost breakdown display.

Args:
parent: Parent frame
"""
sections = [('Materials', 'materials_frame'), ('Labor',
'labor_frame'), ('Hardware', 'hardware_frame'), ('Overhead',
'overhead_frame')]
self.cost_frames = {}
for title, frame_name in sections:
    pass
frame = ttk.LabelFrame(parent, text=title)
frame.pack(fill=tk.X, padx=5, pady=5)
self.cost_frames[frame_name] = frame
total_frame = ttk.Frame(parent)
total_frame.pack(fill=tk.X, padx=5, pady=10)
ttk.Label(total_frame, text='Total Cost:', font=('TkDefaultFont',
10, 'bold')).pack(side=tk.LEFT)
self.total_var = tk.StringVar()
ttk.Label(total_frame, textvariable=self.total_var, font=(
'TkDefaultFont', 12, 'bold')).pack(side=tk.LEFT, padx=5)

@inject(MaterialService)
def create_profitability_analysis(self, parent: ttk.Frame) -> None:
"""
Create the profitability analysis display.

Args:
parent: Parent frame
"""
metrics_frame = ttk.Frame(parent)
metrics_frame.pack(fill=tk.X, pady=5)
self.profit_vars = {}
row = 0
col = 0
metrics = [('Target Price', 'target_price'), ('Actual Cost',
'actual_cost'), ('Gross Profit', 'gross_profit'), (
'Profit Margin', 'profit_margin'), ('Break-Even Point',
'break_even'), ('ROI', 'roi')]
for label, var_name in metrics:
    pass
metric_frame = ttk.Frame(metrics_frame)
metric_frame.grid(row=row, column=col, padx=5,
pady=2, sticky='nsew')
ttk.Label(metric_frame, text=label + ':', font=('TkDefaultFont',
9, 'bold')).pack(anchor=tk.W)
var = tk.StringVar()
self.profit_vars[var_name] = var
ttk.Label(metric_frame, textvariable=var, font=('TkDefaultFont',
12)).pack(anchor=tk.W)
col += 1
if col > 2:
    pass
col = 0
row += 1
for i in range(3):
    pass
metrics_frame.grid_columnconfigure(i, weight=1)
margin_frame = ttk.Frame(parent)
margin_frame.pack(fill=tk.X, pady=10)
ttk.Label(margin_frame, text='Target Margin (%):').pack(side=tk.LEFT)
self.margin_var = tk.StringVar(value='40')
margin_scale = ttk.Scale(margin_frame, from_=0, to=100, orient=tk.
HORIZONTAL, variable=self.margin_var, command=self.
update_profitability)
margin_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
self.profit_canvas = tk.Canvas(parent, bg='white', height=200)
self.profit_canvas.pack(fill=tk.BOTH, expand=True, pady=10)

@inject(MaterialService)
def create_pricing_recommendations(self, parent: ttk.Frame) -> None:
"""
Create the pricing recommendations display.

Args:
parent: Parent frame
"""
points_frame = ttk.LabelFrame(parent, text='Recommended Price Points')
points_frame.pack(fill=tk.X, padx=5, pady=5)
self.price_vars = {}
for label, var_name in [('Economy', 'economy_price'), ('Standard',
'standard_price'), ('Premium', 'premium_price')]:
frame = ttk.Frame(points_frame)
frame.pack(fill=tk.X, pady=2)
ttk.Label(frame, text=f'{label}:').pack(side=tk.LEFT)
var = tk.StringVar()
self.price_vars[var_name] = var
ttk.Label(frame, textvariable=var, font=('TkDefaultFont', 10,
'bold')).pack(side=tk.LEFT, padx=5)
analysis_frame = ttk.LabelFrame(parent, text='Market Analysis')
analysis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
self.market_text = tk.Text(analysis_frame, wrap=tk.WORD, height=8,
state=tk.DISABLED)
self.market_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
comp_frame = ttk.LabelFrame(parent, text='Competitor Comparison')
comp_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
self.comp_canvas = tk.Canvas(comp_frame, bg='white', height=150)
self.comp_canvas.pack(fill=tk.BOTH, expand=True, pady=5)

@inject(MaterialService)
def load_projects(self) -> None:
"""Load and display project list."""
try:
    pass
project_type = None if self.type_var.get(
) == 'ALL' else ProjectType[self.type_var.get()]
projects = self.project_service.search_projects({'project_type':
project_type})
self.project_tree.delete(*self.project_tree.get_children())
for project in projects:
    pass
materials_cost = self.calculate_materials_cost(project)
total_cost = self.calculate_total_cost(project)
values = (project.name, project.project_type.name, project.
status.name, f'${materials_cost:.2f}', f'${total_cost:.2f}'
)
self.project_tree.insert('', tk.END, values=values, tags=(
str(project.id),))
except Exception as e:
    pass
logger.error(f'Error loading projects: {str(e)}')
self.status_var.set('Error loading projects')

@inject(MaterialService)
def calculate_materials_cost(self, project: Project) -> Decimal:
"""
Calculate total materials cost for a project.

Args:
project: Project to calculate for

Returns:
    pass
Total materials cost
"""
total = Decimal('0')
try:
    pass
for component in project.components:
    pass
if component.material_type == MaterialType.LEATHER:
    pass
material = self.material_service.get_material(component
.material_id)
total += material.unit_cost * component.area
else:
material = self.material_service.get_material(component
.material_id)
total += material.unit_cost * component.quantity
except Exception as e:
    pass
logger.error(f'Error calculating materials cost: {str(e)}')
return total

@inject(MaterialService)
def calculate_component_cost(self, component: Any) -> Decimal:
"""
Calculate cost for a specific component.

Args:
component: Project component

Returns:
Component cost
"""
try:
    pass
material = self.material_service.get_material(component.material_id
)
if component.material_type == MaterialType.LEATHER:
    pass
return material.unit_cost * component.area
else:
return material.unit_cost * component.quantity
except Exception as e:
    pass
logger.error(f'Error calculating component cost: {str(e)}')
return Decimal('0')

@inject(MaterialService)
def calculate_total_cost(self, project: Project) -> Decimal:
"""
Calculate total project cost including labor and overhead.

Args:
project: Project to calculate for

Returns:
    pass
Total project cost
"""
try:
    pass
materials_cost = self.calculate_materials_cost(project)
labor_hours = project.estimated_hours or Decimal('0')
labor_cost = labor_hours * self.labor_rate
base_cost = materials_cost + labor_cost
overhead_rate = Decimal('0.15')
overhead_cost = base_cost * overhead_rate
return materials_cost + labor_cost + overhead_cost
except Exception as e:
    pass
logger.error(f'Error calculating total cost: {str(e)}')
return Decimal('0')

@inject(MaterialService)
def update_cost_breakdown(self) -> None:
"""Update the cost breakdown display."""
if not self.current_project:
    pass
return
try:
    pass
materials_cost = self.calculate_materials_cost(self.current_project
)
labor_hours = self.current_project.estimated_hours or Decimal('0')
labor_cost = labor_hours * self.labor_rate
base_cost = materials_cost + labor_cost
overhead_cost = base_cost * Decimal('0.15')
materials_frame = self.cost_frames['materials_frame']
for widget in materials_frame.winfo_children():
    pass
widget.destroy()
for component in self.current_project.components:
    pass
cost = self.calculate_component_cost(component)
frame = ttk.Frame(materials_frame)
frame.pack(fill=tk.X, pady=1)
ttk.Label(frame, text=component.name).pack(side=tk.LEFT)
ttk.Label(frame, text=f'${cost:.2f}').pack(side=tk.RIGHT)
labor_frame = self.cost_frames['labor_frame']
for widget in labor_frame.winfo_children():
    pass
widget.destroy()
ttk.Label(labor_frame, text=f'Hours: {labor_hours}').pack(
side=tk.LEFT)
ttk.Label(labor_frame, text=f'Rate: ${self.labor_rate}/hr').pack(
side=tk.LEFT, padx=10)
ttk.Label(labor_frame, text=f'Total: ${labor_cost:.2f}').pack(
side=tk.RIGHT)
overhead_frame = self.cost_frames['overhead_frame']
for widget in overhead_frame.winfo_children():
    pass
widget.destroy()
ttk.Label(overhead_frame, text='15% of base cost').pack(side=tk
.LEFT)
ttk.Label(overhead_frame, text=f'${overhead_cost:.2f}').pack(
side=tk.RIGHT)
total_cost = materials_cost + labor_cost + overhead_cost
self.total_var.set(f'${total_cost:.2f}')
self.cost_data = {'materials': materials_cost, 'labor':
labor_cost, 'overhead': overhead_cost, 'total': total_cost}
self.update_profitability()
self.update_pricing_recommendations()
except Exception as e:
    pass
logger.error(f'Error updating cost breakdown: {str(e)}')
self.status_var.set('Error updating cost breakdown')

@inject(MaterialService)
def on_project_select(self, event: Any) -> None:
"""
Handle project selection in the treeview.

Args:
event: Event data
"""
selection = self.project_tree.selection()
if not selection:
    pass
return
try:
    pass
project_id = int(self.project_tree.item(selection[0], 'tags')[0])
self.current_project = self.project_service.get_project(project_id,
include_components=True)
self.update_cost_breakdown()
except Exception as e:
    pass
logger.error(f'Error loading project details: {str(e)}')
self.status_var.set('Error loading project details')

@inject(MaterialService)
def cleanup(self) -> None:
"""Perform cleanup before view is destroyed."""
try:
    pass
self.save_settings()
except Exception as e:
    pass
logger.error(f'Error during cleanup: {str(e)}')

@inject(MaterialService)
def load_settings(self) -> None:
"""Load saved settings."""
try:
    pass
with open('cost_analyzer_settings.json', 'r') as f:
    pass
settings = json.load(f)
self.labor_rate = Decimal(str(settings.get('labor_rate',
'25.00')))
self.labor_var.set(str(self.labor_rate))
except Exception as e:
    pass
logger.error(f'Error loading settings: {str(e)}')

@inject(MaterialService)
def save_settings(self) -> None:
"""Save current settings."""
try:
    pass
settings = {'labor_rate': str(self.labor_rate)}
with open('cost_analyzer_settings.json', 'w') as f:
    pass
json.dump(settings, f)
except Exception as e:
    pass
logger.error(f'Error saving settings: {str(e)}')

@inject(MaterialService)
def update_labor_rate(self, *args) -> None:
"""Update the labor rate when changed."""
try:
    pass
new_rate = Decimal(self.labor_var.get())
if new_rate <= 0:
    pass
raise ValueError('Labor rate must be positive')
self.labor_rate = new_rate
self.save_settings()
if self.current_project:
    pass
self.update_cost_breakdown()
except ValueError:
    pass
self.labor_var.set(str(self.labor_rate))

@inject(MaterialService)
def update_profitability(self, *args) -> None:
"""Update the profitability analysis display."""
if not self.current_project or not self.cost_data:
    pass
return
try:
    pass
target_margin = Decimal(self.margin_var.get()) / 100
total_cost = self.cost_data['total']
target_price = total_cost / (1 - target_margin)
gross_profit = target_price - total_cost
metrics = {'target_price': f'${target_price:.2f}',
'actual_cost': f'${total_cost:.2f}', 'gross_profit':
f'${gross_profit:.2f}', 'profit_margin':
f'{target_margin * 100:.1f}%', 'break_even':
f'{total_cost / target_price * 100:.1f}% of price', 'roi':
f'{gross_profit / total_cost * 100:.1f}%'}
for name, value in metrics.items():
    pass
self.profit_vars[name].set(value)
self.update_profitability_chart(total_cost, target_price)
except Exception as e:
    pass
logger.error(f'Error updating profitability: {str(e)}')
self.status_var.set('Error updating profitability analysis')
