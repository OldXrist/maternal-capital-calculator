import sys
import math

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea
)
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter


DENOM = 1000


def fraction_to_str(numerator, denominator=DENOM):
    return f"{numerator}/{denominator}"


class MaternalCapitalCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор долей с материнским капиталом")
        self.setGeometry(100, 100, 800, 900)

        self.children_name_edits = []
        self.children_names = []

        self._build_ui()
        self.update_children_fields()

    # ------------------------------------------------ UI

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        main_layout.addLayout(self._build_inputs())
        main_layout.addWidget(self._build_children_block())

        self.calculate_button = QPushButton("Рассчитать доли")
        self.calculate_button.clicked.connect(self.calculate_shares)
        main_layout.addWidget(self.calculate_button)

        main_layout.addWidget(QLabel("Результаты:"))
        self.results_text = QTextEdit(readOnly=True)
        main_layout.addWidget(self.results_text)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        main_layout.addWidget(self.chart_view)

    def _build_inputs(self):
        layout = QGridLayout()

        layout.addWidget(QLabel("Количество детей:"), 0, 0)
        self.num_children_spin = QSpinBox(minimum=0, maximum=30)
        self.num_children_spin.valueChanged.connect(self.update_children_fields)
        layout.addWidget(self.num_children_spin, 0, 1)

        layout.addWidget(QLabel("Стоимость квартиры (руб.):"), 1, 0)
        self.apartment_cost_spin = QDoubleSpinBox(minimum=0, maximum=999_999_999, decimals=2)
        layout.addWidget(self.apartment_cost_spin, 1, 1)

        layout.addWidget(QLabel("Использованный материнский капитал (руб.):"), 2, 0)
        self.maternal_capital_spin = QDoubleSpinBox(minimum=0, maximum=999_999_999, decimals=2)
        layout.addWidget(self.maternal_capital_spin, 2, 1)

        layout.addWidget(QLabel("ФИО родителя 1:"), 3, 0)
        self.parent1_name_edit = QLineEdit()
        layout.addWidget(self.parent1_name_edit, 3, 1)

        layout.addWidget(QLabel("ФИО родителя 2:"), 4, 0)

        row = QHBoxLayout()
        self.parent2_name_edit = QLineEdit()
        row.addWidget(self.parent2_name_edit)

        self.parent2_checkbox = QCheckBox("Участвует")
        self.parent2_checkbox.setChecked(True)
        self.parent2_checkbox.toggled.connect(
            lambda c: self.parent2_name_edit.setEnabled(c)
        )
        row.addWidget(self.parent2_checkbox)

        layout.addLayout(row, 4, 1)
        return layout

    def _build_children_block(self):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)

        layout.addWidget(QLabel("ФИО детей:"))

        self.children_scroll = QScrollArea(widgetResizable=True)
        self.children_scroll.setFixedHeight(120)

        self.children_widget = QWidget()
        self.children_layout = QVBoxLayout(self.children_widget)
        self.children_scroll.setWidget(self.children_widget)

        layout.addWidget(self.children_scroll)
        return wrapper

    # ------------------------------------------------ Children fields

    def update_children_fields(self):
        count = self.num_children_spin.value()

        if self.children_name_edits:
            self.children_names = [e.text().strip() for e in self.children_name_edits]

        self._clear_layout(self.children_layout)
        self.children_name_edits.clear()

        self.children_names = (
            self.children_names[:count]
            + [""] * max(0, count - len(self.children_names))
        )

        if count == 0:
            label = QLabel("Нет детей")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.children_layout.addWidget(label)
            return

        for i in range(count):
            row = QHBoxLayout()
            row.addWidget(QLabel(f"Ребенок {i + 1}:"))
            edit = QLineEdit(self.children_names[i])
            row.addWidget(edit)
            self.children_layout.addLayout(row)
            self.children_name_edits.append(edit)

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                MaternalCapitalCalculator._clear_layout(item.layout())

    # ------------------------------------------------ Calculation

    def calculate_shares(self):
        try:
            num_children = self.num_children_spin.value()
            apartment_cost = self.apartment_cost_spin.value()
            maternal_capital = self.maternal_capital_spin.value()

            if apartment_cost <= 0:
                raise ValueError("Стоимость квартиры должна быть положительной.")
            if maternal_capital < 0 or maternal_capital > apartment_cost:
                raise ValueError("Материнский капитал вне допустимого диапазона.")

            two_parents = self.parent2_checkbox.isChecked()
            num_parents = 2 if two_parents else 1

            parent1_name = self.parent1_name_edit.text().strip() or "Родитель 1"
            parent2_name = self.parent2_name_edit.text().strip() or "Родитель 2"

            children_names = [
                e.text().strip() or f"Ребенок {i+1}"
                for i, e in enumerate(self.children_name_edits)
            ]

            # ---------------- BASE SHARES ----------------

            m_share = maternal_capital / apartment_cost
            mc_num = round(m_share * DENOM)
            non_mc_num = DENOM - mc_num

            total_participants = num_parents + num_children
            m_per_float = m_share / total_participants if total_participants else 0
            child_share_num = math.ceil(m_per_float * DENOM) if num_children else 0

            total_children_num = child_share_num * num_children
            remaining_mc_num = mc_num - total_children_num

            # ---------------- PARENTS ----------------

            if num_parents == 2:
                parent_without_num = non_mc_num // 2
                parent_m_num = round(remaining_mc_num / 2)
                parent1_total = parent2_total = parent_without_num + parent_m_num

                total = parent1_total * 2 + total_children_num
                delta = DENOM - total

                if delta:
                    half = delta // 2
                    parent1_total += half
                    parent2_total += half
                    if delta % 2:
                        parent1_total += 1
                        parent1_total = parent2_total = min(parent1_total, parent2_total)

            else:
                parent_without_num = non_mc_num
                parent1_total = non_mc_num + remaining_mc_num
                parent2_total = 0

            # ---------------- FINAL SAFETY ----------------

            final_sum = parent1_total + parent2_total + total_children_num
            delta = DENOM - final_sum

            if delta != 0:
                if num_children > 0:
                    # Push rounding error into children first
                    child_share_num += delta // num_children
                else:
                    # No children → split between parents
                    half = delta // 2
                    parent1_total += half
                    parent2_total += half

            # ---------------- OUTPUT ----------------

            result = (
                f"Доля мат. капитала в жилом помещении: {fraction_to_str(mc_num)}\n"
                f"Доля собственных средств в жилом помещении: {fraction_to_str(non_mc_num)}\n\n"
            )

            result += "• Доли без учета мат. капитала •\n"
            result += f"{parent1_name}: {fraction_to_str(parent1_total - child_share_num)}\n"
            if two_parents:
                result += f"{parent2_name}: {fraction_to_str(parent1_total - child_share_num)}\n"

            result += "\n• Доли с учетом мат. капитала •\n"
            result += f"{parent1_name}: {fraction_to_str(parent1_total)}\n"
            if two_parents:
                result += f"{parent2_name}: {fraction_to_str(parent2_total)}\n"
            for child in children_names:
                result += f"{child}: {fraction_to_str(child_share_num)}\n"

            self.results_text.setText(result)

            series = QPieSeries()
            series.append(parent1_name, parent1_total / DENOM * 100)
            if two_parents:
                series.append(parent2_name, parent2_total / DENOM * 100)
            for child in children_names:
                series.append(child, child_share_num / DENOM * 100)

            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("Распределение долей (%)")
            chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
            self.chart_view.setChart(chart)

        except Exception as e:
            self.results_text.setText(f"Ошибка: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MaternalCapitalCalculator()
    window.show()
    sys.exit(app.exec())
