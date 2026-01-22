import sys
import math
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QGridLayout, QScrollArea)
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QIcon


def fraction_to_str(numerator, denominator=1000):
    """Convert numerator/denominator to string like '444/1000'"""
    return f"{numerator}/{denominator}"


class MaternalCapitalCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор долей с материнским капиталом")
        self.setGeometry(100, 100, 800, 900)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Input section
        input_layout = QGridLayout()

        # Number of children
        input_layout.addWidget(QLabel("Количество детей:"), 0, 0)
        self.num_children_spin = QSpinBox()
        self.num_children_spin.setMinimum(0)
        self.num_children_spin.setMaximum(30)
        self.num_children_spin.valueChanged.connect(self.update_children_fields)
        input_layout.addWidget(self.num_children_spin, 0, 1)

        # Apartment cost
        input_layout.addWidget(QLabel("Стоимость квартиры (руб.):"), 1, 0)
        self.apartment_cost_spin = QDoubleSpinBox()
        self.apartment_cost_spin.setMinimum(0.0)
        self.apartment_cost_spin.setMaximum(999999999.0)
        self.apartment_cost_spin.setDecimals(2)
        input_layout.addWidget(self.apartment_cost_spin, 1, 1)

        # Maternal capital
        input_layout.addWidget(QLabel("Использованный материнский капитал (руб.):"), 2, 0)
        self.maternal_capital_spin = QDoubleSpinBox()
        self.maternal_capital_spin.setMinimum(0.0)
        self.maternal_capital_spin.setMaximum(999999999.0)
        self.maternal_capital_spin.setDecimals(2)
        input_layout.addWidget(self.maternal_capital_spin, 2, 1)

        # Parent names
        input_layout.addWidget(QLabel("ФИО родителя 1 (опционально):"), 3, 0)
        self.parent1_name_edit = QLineEdit()
        input_layout.addWidget(self.parent1_name_edit, 3, 1)

        input_layout.addWidget(QLabel("ФИО родителя 2 (опционально):"), 4, 0)
        self.parent2_name_edit = QLineEdit()
        input_layout.addWidget(self.parent2_name_edit, 4, 1)

        main_layout.addLayout(input_layout)

        # Dynamic children names section
        self.children_scroll = QScrollArea()
        self.children_scroll.setWidgetResizable(True)
        self.children_scroll.setFixedHeight(100)
        self.children_widget = QWidget()
        self.children_layout = QVBoxLayout(self.children_widget)
        self.children_scroll.setWidget(self.children_widget)
        main_layout.addWidget(QLabel("ФИО детей (опционально):"))
        main_layout.addWidget(self.children_scroll)

        # Initialize children_name_edits BEFORE initial update
        self.children_name_edits = []
        self.children_names = []

        # Initial update (0 children)
        self.update_children_fields()

        # Calculate button
        self.calculate_button = QPushButton("Рассчитать доли")
        self.calculate_button.clicked.connect(self.calculate_shares)
        main_layout.addWidget(self.calculate_button)

        # Results text area
        main_layout.addWidget(QLabel("Результаты:"))
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        main_layout.addWidget(self.results_text)

        # Pie chart (to make it bigger, uncomment and adjust the next two lines:
        # self.chart_view.setFixedSize(600, 400)  # Example: set fixed size
        self.chart_view = QChartView()
        self.chart_view.setMinimumSize(500, 300)  # Or set minimum size for layout expansion
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        main_layout.addWidget(self.chart_view)

    def update_children_fields(self):
        num_children = self.num_children_spin.value()

        # Save current names if fields exist
        if self.children_name_edits:
            self.children_names = [edit.text().strip() for edit in self.children_name_edits]

        # Clear existing fields and layouts properly
        while self.children_layout.count():
            item = self.children_layout.takeAt(0)
            if item:
                if isinstance(item, QHBoxLayout):
                    # Clear sub-widgets in horizontal layout
                    while item.count():
                        sub_item = item.takeAt(0)
                        if sub_item.widget():
                            sub_item.widget().setParent(None)
                    # No need for del item; takeAt removes it
                elif item.widget():
                    item.widget().setParent(None)

        self.children_name_edits.clear()

        # Resize persisted names to match new num_children
        self.children_names = self.children_names[:num_children] + [""] * max(0, num_children - len(self.children_names))

        # Add new fields inline (horizontal)
        for i in range(num_children):
            child_layout = QHBoxLayout()
            label = QLabel(f"Ребенок {i + 1}:")
            edit = QLineEdit()
            edit.setText(self.children_names[i])  # Restore persisted name
            child_layout.addWidget(label)
            child_layout.addWidget(edit)
            self.children_layout.addLayout(child_layout)
            self.children_name_edits.append(edit)

        # If no children, add a note
        if num_children == 0:
            note = QLabel("Нет детей")
            note.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.children_layout.addWidget(note)

    def calculate_shares(self):
        try:
            # Get inputs
            num_children = self.num_children_spin.value()
            apartment_cost = self.apartment_cost_spin.value()
            maternal_capital = self.maternal_capital_spin.value()

            if apartment_cost <= 0:
                raise ValueError("Стоимость квартиры должна быть положительной.")
            if maternal_capital < 0 or maternal_capital > apartment_cost:
                raise ValueError("Материнский капитал должен быть между 0 и стоимостью квартиры.")

            # Get names
            parent1_name = self.parent1_name_edit.text().strip() or "Родитель 1"
            parent2_name = self.parent2_name_edit.text().strip() or "Родитель 2"
            children_names = []
            for edit in self.children_name_edits:
                name = edit.text().strip()
                children_names.append(name or f"Ребенок {len(children_names) + 1}")

            # Calculations
            DENOM = 1000
            m_share = maternal_capital / apartment_cost
            mc_num = round(m_share * DENOM)
            non_mc_num = DENOM - mc_num
            parent_without_num = non_mc_num // 2  # Floor division for equality

            total_participants = 2 + num_children
            m_per_float = m_share / total_participants if total_participants > 0 else 0

            if num_children > 0:
                child_share_num = math.ceil(m_per_float * DENOM)
                total_children_num = child_share_num * num_children
                remaining_mc_num = mc_num - total_children_num
                parent_m_num = round(remaining_mc_num / 2.0)
            else:
                child_share_num = 0
                total_children_num = 0
                remaining_mc_num = mc_num
                parent_m_num = round(remaining_mc_num / 2.0)

            # Base totals
            parent_base_num = parent_without_num + parent_m_num
            total_so_far = 2 * parent_base_num + total_children_num
            excess = total_so_far - DENOM

            # Initial totals
            parent1_total_num = parent_base_num
            parent2_total_num = parent_base_num

            if excess > 0:
                # Adjust excess
                adjust = excess // 2
                parent1_total_num -= adjust
                parent2_total_num -= adjust
                rem = excess % 2
                if rem > 0:
                    # Subtract rem from parent2
                    parent2_total_num -= rem
                    # Now equalize if unequal
                    if parent1_total_num > parent2_total_num:
                        diff = parent1_total_num - parent2_total_num
                        parent1_total_num -= diff
                        extra_adjust = diff
                        # Distribute extra_adjust (1 typically) to children
                        if num_children > 0 and extra_adjust > 0:
                            extra = extra_adjust / DENOM / num_children
                            new_m_per_float = m_per_float + extra
                            new_child_share_num = math.ceil(new_m_per_float * DENOM)
                            child_share_num = new_child_share_num
                    elif parent2_total_num > parent1_total_num:
                        diff = parent2_total_num - parent1_total_num
                        parent2_total_num -= diff
                        extra_adjust = diff
                        if num_children > 0 and extra_adjust > 0:
                            extra = extra_adjust / DENOM / num_children
                            new_m_per_float = m_per_float + extra
                            new_child_share_num = math.ceil(new_m_per_float * DENOM)
                            child_share_num = new_child_share_num
            elif excess < 0:
                # Adjust shortfall (add)
                shortfall = -excess
                adjust = shortfall // 2
                parent1_total_num += adjust
                parent2_total_num += adjust
                rem = shortfall % 2
                if rem > 0:
                    # Add rem to parent1
                    parent1_total_num += rem
                    # If now unequal, but since added to one, to equalize would require adding to other, creating extra add
                    # For simplicity, accept inequality of rem (1)
                    pass

            # Ensure equal parents if possible (force average floor)
            if parent1_total_num != parent2_total_num:
                avg = (parent1_total_num + parent2_total_num) // 2
                parent1_total_num = avg
                parent2_total_num = avg
                # This may cause further shortfall, but for now, accept

            # Ensure non-negative
            parent1_total_num = max(0, parent1_total_num)
            parent2_total_num = max(0, parent2_total_num)

            # Recalculate parent's shares after adjustment
            parent_without_num = parent1_total_num - child_share_num

            # Results text
            results = "• Доли супругов без учета мат. капитала •\n"
            results += f"{parent1_name}: {fraction_to_str(parent_without_num)}\n"
            results += f"{parent2_name}: {fraction_to_str(parent_without_num)}\n\n"

            results += "• Доли всех участников в части, приобретенной за счет мат.капитала •\n"
            results += f"{parent1_name}: {fraction_to_str(child_share_num)}\n"
            results += f"{parent2_name}: {fraction_to_str(child_share_num)}\n"
            for i, child_name in enumerate(children_names):
                results += f"{child_name}: {fraction_to_str(child_share_num)}\n"
            results += "\n"

            results += "• Доли всех участников с учётом мат. капитала •\n"
            results += f"{parent1_name}: {fraction_to_str(parent1_total_num)}\n"
            results += f"{parent2_name}: {fraction_to_str(parent2_total_num)}\n"
            for i, child_name in enumerate(children_names):
                results += f"{child_name}: {fraction_to_str(child_share_num)}\n"

            self.results_text.setText(results)

            # Pie chart (using the final values for visualization)
            parent1_total_float = parent1_total_num / DENOM
            parent2_total_float = parent2_total_num / DENOM
            child_total_float = child_share_num / DENOM
            series = QPieSeries()
            series.append(parent1_name, parent1_total_float * 100)
            series.append(parent2_name, parent2_total_float * 100)
            for child_name in children_names:
                series.append(child_name, child_total_float * 100)

            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("Распределение долей в квартире (%)")
            chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)

            self.chart_view.setChart(chart)

        except ValueError as e:
            self.results_text.setText(f"Ошибка: {str(e)}")
        except Exception as e:
            self.results_text.setText(f"Неожиданная ошибка: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MaternalCapitalCalculator()
    window.show()
    sys.exit(app.exec())
