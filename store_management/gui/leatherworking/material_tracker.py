from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
logger = logging.getLogger(__name__)


class MaterialUsageTracker(BaseView):
    """
    Track and analyze material usage across projects.
    Provides visualization and analytics for material consumption,
    waste tracking, and efficiency metrics.
    """

        @inject(MaterialService)
        def __init__(self, parent: tk.Widget, app: Any) ->None:
        """
        Initialize the material usage tracker.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.material_service = self.get_service(IMaterialService)
        self.inventory_service = self.get_service(IInventoryService)
        self.error_handler = ErrorHandler()
        self.current_material_id: Optional[int] = None
        self.usage_data: List[MaterialUsageLog] = []
        self.time_range = 'month'
        self.setup_ui()
        self.load_data()

        @inject(MaterialService)
        def setup_ui(self) ->None:
        """Create and configure the UI components."""
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)
        self.content = ttk.Frame(self)
        self.content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.create_toolbar()
        self.create_material_list()
        self.create_analytics_section()
        self.create_visualization()
        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN).pack(
            fill=tk.X, pady=(5, 0))

        @inject(MaterialService)
        def create_toolbar(self) ->None:
        """Create toolbar controls."""
        ttk.Label(self.toolbar, text='Material Type:').pack(side=tk.LEFT,
            padx=5)
        self.type_var = tk.StringVar(value='ALL')
        type_combo = ttk.Combobox(self.toolbar, textvariable=self.type_var,
            values=['ALL'] + [t.name for t in MaterialType], state=
            'readonly', width=15)
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind('<<ComboboxSelected>>', lambda _: self.load_data())
        ttk.Label(self.toolbar, text='Time Range:').pack(side=tk.LEFT, padx=5)
        self.range_var = tk.StringVar(value='month')
        for text, value in [('Week', 'week'), ('Month', 'month'), ('Year',
            'year')]:
            ttk.Radiobutton(self.toolbar, text=text, variable=self.
                range_var, value=value, command=self.update_visualization
                ).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text='Export Data', command=self.export_data
            ).pack(side=tk.RIGHT, padx=5)

        @inject(MaterialService)
        def create_material_list(self) ->None:
        """Create the material list section."""
        frame = ttk.LabelFrame(self.content, text='Materials')
        frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        columns = 'name', 'type', 'usage', 'efficiency'
        self.material_tree = ttk.Treeview(frame, columns=columns, show=
            'headings', height=15)
        headings = {'name': 'Material Name', 'type': 'Type', 'usage':
            'Total Usage', 'efficiency': 'Efficiency'}
        for col, heading in headings.items():
            self.material_tree.heading(col, text=heading)
            self.material_tree.column(col, width=100)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.
            material_tree.yview)
        self.material_tree.configure(yscrollcommand=scrollbar.set)
        self.material_tree.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.material_tree.bind('<<TreeviewSelect>>', self.on_material_select)

        @inject(MaterialService)
        def create_analytics_section(self) ->None:
        """Create the analytics and metrics section."""
        frame = ttk.LabelFrame(self.content, text='Analytics')
        frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        metrics_frame = ttk.Frame(frame)
        metrics_frame.pack(fill=tk.X, pady=5)
        self.metric_vars = {}
        row = 0
        col = 0
        metrics = [('Total Usage', 'total_usage'), ('Average per Project',
            'avg_per_project'), ('Efficiency Rate', 'efficiency_rate'), (
            'Waste Rate', 'waste_rate'), ('Cost per Unit', 'cost_per_unit'),
            ('Projected Usage', 'projected_usage')]
        for label, var_name in metrics:
            metric_frame = ttk.Frame(metrics_frame)
            metric_frame.grid(row=row, column=col, padx=5, pady=2, sticky=
                'nsew')
            ttk.Label(metric_frame, text=label + ':', font=('TkDefaultFont',
                9, 'bold')).pack(anchor=tk.W)
            var = tk.StringVar()
            self.metric_vars[var_name] = var
            ttk.Label(metric_frame, textvariable=var, font=('TkDefaultFont',
                12)).pack(anchor=tk.W)
            col += 1
            if col > 2:
                col = 0
                row += 1
        metrics_frame.grid_columnconfigure(0, weight=1)
        metrics_frame.grid_columnconfigure(1, weight=1)
        metrics_frame.grid_columnconfigure(2, weight=1)
        trend_frame = ttk.LabelFrame(frame, text='Usage Trends')
        trend_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.trend_text = tk.Text(trend_frame, height=4, wrap=tk.WORD,
            state=tk.DISABLED)
        self.trend_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        @inject(MaterialService)
        def create_visualization(self) ->None:
        """Create the data visualization section."""
        frame = ttk.LabelFrame(self.content, text='Usage Visualization')
        frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.canvas = tk.Canvas(frame, bg='white', width=600, height=300)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        legend_frame = ttk.Frame(frame)
        legend_frame.pack(fill=tk.X, pady=5)
        legend_items = [('Usage', 'blue'), ('Waste', 'red'), ('Efficiency',
            'green')]
        for text, color in legend_items:
            item_frame = ttk.Frame(legend_frame)
            item_frame.pack(side=tk.LEFT, padx=10)
            canvas = tk.Canvas(item_frame, width=15, height=15)
            canvas.create_rectangle(0, 0, 15, 15, fill=color)
            canvas.pack(side=tk.LEFT)
            ttk.Label(item_frame, text=text).pack(side=tk.LEFT, padx=2)

        @inject(MaterialService)
        def load_data(self) ->None:
        """Load and display material usage data."""
        try:
            material_type = None if self.type_var.get(
                ) == 'ALL' else MaterialType[self.type_var.get()]
            materials = self.material_service.get_all_materials(material_type)
            self.material_tree.delete(*self.material_tree.get_children())
            for material in materials:
                stats = self.material_service.get_material_efficiency_stats(
                    material.id, days=self.get_days_for_range())
                values = (material.name, material.material_type.name,
                    f"{stats['total_usage']:.2f}",
                    f"{stats['efficiency']:.1f}%")
                self.material_tree.insert('', tk.END, values=values, tags=(
                    str(material.id),))
        except Exception as e:
            logger.error(f'Error loading material data: {str(e)}')
            self.status_var.set('Error loading material data')

        @inject(MaterialService)
        def on_material_select(self, event: Any) ->None:
        """
        Handle material selection in the treeview.

        Args:
            event: Event data
        """
        selection = self.material_tree.selection()
        if not selection:
            return
        try:
            material_id = int(self.material_tree.item(selection[0], 'tags')[0])
            self.current_material_id = material_id
            self.load_material_data(material_id)
            self.update_visualization()
        except Exception as e:
            logger.error(f'Error loading material details: {str(e)}')
            self.status_var.set('Error loading material details')

        @inject(MaterialService)
        def load_material_data(self, material_id: int) ->None:
        """
        Load detailed data for a specific material.

        Args:
            material_id: ID of material to load
        """
        try:
            self.usage_data = self.material_service.get_material_usage_history(
                material_id, days=self.get_days_for_range())
            self.update_metrics()
            self.update_trend_analysis()
        except Exception as e:
            logger.error(f'Error loading material details: {str(e)}')
            self.status_var.set('Error loading material details')

        @inject(MaterialService)
        def update_metrics(self) ->None:
        """Update the metrics display with current data."""
        if not self.usage_data:
            return
        total_usage = sum(log.quantity_used for log in self.usage_data)
        total_waste = sum(log.waste_amount for log in self.usage_data)
        num_projects = len({log.project_id for log in self.usage_data})
        metrics = {'total_usage': f'{total_usage:.2f} units',
            'avg_per_project': f'{total_usage / num_projects:.2f} units' if
            num_projects else 'N/A', 'efficiency_rate': 
            f'{(total_usage - total_waste) / total_usage * 100:.1f}%' if
            total_usage else 'N/A', 'waste_rate': 
            f'{total_waste / total_usage * 100:.1f}%' if total_usage else
            'N/A', 'cost_per_unit': self.calculate_cost_per_unit(),
            'projected_usage': self.calculate_projected_usage()}
        for name, value in metrics.items():
            self.metric_vars[name].set(value)

        @inject(MaterialService)
        def calculate_cost_per_unit(self) ->str:
        """
        Calculate the average cost per unit of material.

        Returns:
            Formatted cost string
        """
        if not self.current_material_id:
            return 'N/A'
        try:
            material = self.material_service.get_material(self.
                current_material_id)
            recent_orders = self.material_service.get_recent_orders(self.
                current_material_id, days=90)
            if not recent_orders:
                return f'${material.unit_cost:.2f}'
            avg_cost = sum(o.unit_price for o in recent_orders) / len(
                recent_orders)
            return f'${avg_cost:.2f}'
        except Exception as e:
            logger.error(f'Error calculating cost per unit: {str(e)}')
            return 'Error'

        @inject(MaterialService)
        def calculate_projected_usage(self) ->str:
        """
        Calculate projected usage based on historical data.

        Returns:
            Formatted projection string
        """
        if not self.usage_data:
            return 'N/A'
        try:
            days = self.get_days_for_range()
            total_usage = sum(log.quantity_used for log in self.usage_data)
            daily_avg = total_usage / days
            projection = daily_avg * days
            return f'{projection:.2f} units'
        except Exception as e:
            logger.error(f'Error calculating projection: {str(e)}')
            return 'Error'

        @inject(MaterialService)
        def update_trend_analysis(self) ->None:
        """Update the trend analysis text."""
        if not self.usage_data:
            self.trend_text.configure(state=tk.NORMAL)
            self.trend_text.delete('1.0', tk.END)
            self.trend_text.insert(tk.END, 'No usage data available.')
            self.trend_text.configure(state=tk.DISABLED)
            return
        try:
            current_period = sum(log.quantity_used for log in self.
                usage_data if (datetime.now() - log.date).days <= self.
                get_days_for_range() // 2)
            previous_period = sum(log.quantity_used for log in self.
                usage_data if self.get_days_for_range() >= (datetime.now() -
                log.date).days > self.get_days_for_range() // 2)
            change_pct = (current_period - previous_period
                ) / previous_period * 100 if previous_period else 0
            trend_text = []
            trend_text.append('Usage Trend: ')
            if abs(change_pct) < 5:
                trend_text.append('Stable usage pattern. ')
            else:
                trend_text.append(
                    f"{'Increased' if change_pct > 0 else 'Decreased'} by {abs(change_pct):.1f}%. "
                    )
            current_efficiency = self.calculate_period_efficiency(0, self.
                get_days_for_range() // 2)
            previous_efficiency = self.calculate_period_efficiency(self.
                get_days_for_range() // 2, self.get_days_for_range())
            if current_efficiency and previous_efficiency:
                eff_change = current_efficiency - previous_efficiency
                trend_text.append('\nEfficiency: ')
                if abs(eff_change) < 2:
                    trend_text.append('Maintaining consistent efficiency. ')
                else:
                    trend_text.append(
                        f"{'Improved' if eff_change > 0 else 'Declined'} by {abs(eff_change):.1f}%. "
                        )
            if change_pct > 20:
                trend_text.append(
                    """
Recommendation: Consider increasing stock levels to match higher usage."""
                    )
            elif change_pct < -20:
                trend_text.append(
                    '\nRecommendation: Review stock levels to prevent overstock.'
                    )
            self.trend_text.configure(state=tk.NORMAL)
            self.trend_text.delete('1.0', tk.END)
            self.trend_text.insert(tk.END, ''.join(trend_text))
            self.trend_text.configure(state=tk.DISABLED)
        except Exception as e:
            logger.error(f'Error updating trend analysis: {str(e)}')
            self.status_var.set('Error updating trend analysis')

        @inject(MaterialService)
        def calculate_period_efficiency(self, start_days: int, end_days: int
        ) ->Optional[float]:
        """
        Calculate material efficiency for a specific period.

        Args:
            start_days: Start of period (days ago)
            end_days: End of period (days ago)

        Returns:
            Efficiency percentage or None if no data
        """
        try:
            period_logs = [log for log in self.usage_data if end_days >= (
                datetime.now() - log.date).days > start_days]
            if not period_logs:
                return None
            total_used = sum(log.quantity_used for log in period_logs)
            total_waste = sum(log.waste_amount for log in period_logs)
            return (total_used - total_waste
                ) / total_used * 100 if total_used else None
        except Exception as e:
            logger.error(f'Error calculating period efficiency: {str(e)}')
            return None

        @inject(MaterialService)
        def update_visualization(self) ->None:
        """Update the usage visualization chart."""
        if not self.usage_data:
            return
        try:
            self.canvas.delete('all')
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            margin = 40
            periods = self.group_data_by_periods()
            if not periods:
                return
            max_usage = max(data['usage'] for data in periods)
            x_scale = (width - 2 * margin) / (len(periods) - 1)
            y_scale = (height - 2 * margin) / max_usage
            self.draw_axes(margin, width, height)
            self.draw_usage_line(periods, margin, x_scale, y_scale, height)
            self.draw_efficiency_line(periods, margin, x_scale, y_scale, height
                )
            self.draw_period_labels(periods, margin, x_scale, height)
        except Exception as e:
            logger.error(f'Error updating visualization: {str(e)}')
            self.status_var.set('Error updating visualization')

        @inject(MaterialService)
        def group_data_by_periods(self) ->List[Dict[str, Any]]:
        """
        Group usage data into time periods for visualization.

        Returns:
            List of period data dictionaries
        """
        periods = []
        period_length = {'week': timedelta(days=1), 'month': timedelta(days
            =7), 'year': timedelta(days=30)}[self.range_var.get()]
        current_date = datetime.now()
        start_date = current_date - timedelta(days=self.get_days_for_range())
        current_period = start_date
        while current_period <= current_date:
            period_logs = [log for log in self.usage_data if current_period <=
                log.date < current_period + period_length]
            total_usage = sum(log.quantity_used for log in period_logs
                ) if period_logs else 0
            total_waste = sum(log.waste_amount for log in period_logs
                ) if period_logs else 0
            periods.append({'date': current_period, 'usage': total_usage,
                'efficiency': (total_usage - total_waste) / total_usage * 
                100 if total_usage else 0})
            current_period += period_length
        return periods

        @inject(MaterialService)
        def draw_axes(self, margin: int, width: int, height: int) ->None:
        """
        Draw chart axes.

        Args:
            margin: Chart margin
            width: Canvas width
            height: Canvas height
        """
        self.canvas.create_line(margin, height - margin, margin, margin,
            width=2)
        self.canvas.create_line(margin, height - margin, width - margin, 
            height - margin, width=2)

        @inject(MaterialService)
        def draw_usage_line(self, periods: List[Dict[str, Any]], margin: int,
        x_scale: float, y_scale: float, height: int) ->None:
        """
        Draw the usage data line.

        Args:
            periods: Period data
            margin: Chart margin
            x_scale: X-axis scale
            y_scale: Y-axis scale
            height: Canvas height
        """
        points = []
        for i, data in enumerate(periods):
            x = margin + i * x_scale
            y = height - margin - data['usage'] * y_scale
            points.extend([x, y])
        if len(points) >= 4:
            self.canvas.create_line(*points, fill='blue', width=2, smooth=True)

        @inject(MaterialService)
        def draw_efficiency_line(self, periods: List[Dict[str, Any]], margin:
        int, x_scale: float, y_scale: float, height: int) ->None:
        """
        Draw the efficiency data line.

        Args:
            periods: Period data
            margin: Chart margin
            x_scale: X-axis scale
            y_scale: Y-axis scale
            height: Canvas height
        """
        points = []
        max_efficiency = 100
        for i, data in enumerate(periods):
            x = margin + i * x_scale
            y = height - margin - data['efficiency'] / max_efficiency * (height
                 - 2 * margin)
            points.extend([x, y])
        if len(points) >= 4:
            self.canvas.create_line(*points, fill='green', width=2, smooth=
                True, dash=(5, 2))

        @inject(MaterialService)
        def draw_period_labels(self, periods: List[Dict[str, Any]], margin: int,
        x_scale: float, height: int) ->None:
        """
        Draw time period labels.

        Args:
            periods: Period data
            margin: Chart margin
            x_scale: X-axis scale
            height: Canvas height
        """
        format_str = {'week': '%a', 'month': '%d', 'year': '%b'}[self.
            range_var.get()]
        for i, data in enumerate(periods):
            if i % 2 == 0:
                x = margin + i * x_scale
                self.canvas.create_text(x, height - margin + 15, text=data[
                    'date'].strftime(format_str), anchor=tk.N)

        @inject(MaterialService)
        def get_days_for_range(self) ->int:
        """
        Get number of days for current time range.

        Returns:
            Number of days
        """
        return {'week': 7, 'month': 30, 'year': 365}[self.range_var.get()]

        @inject(MaterialService)
        def export_data(self) ->None:
        """Export the current material usage data."""
        if not self.current_material_id:
            tk.messagebox.showwarning('Export',
                'Please select a material to export data for.')
            return
        try:
            file_path = tk.filedialog.asksaveasfilename(defaultextension=
                '.csv', filetypes=[('CSV files', '*.csv'), ('All files',
                '*.*')])
            if not file_path:
                return
            self.material_service.export_usage_data(self.
                current_material_id, file_path, self.get_days_for_range())
            tk.messagebox.showinfo('Export', 'Data exported successfully.')
        except Exception as e:
            logger.error(f'Error exporting data: {str(e)}')
            tk.messagebox.showerror('Export Error',
                'Failed to export data. Please check the logs for details.')
