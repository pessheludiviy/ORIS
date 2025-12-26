import threading
import queue
import time
import random
from datetime import datetime
from enum import Enum


class OrderStatus(Enum):
    PENDING = "ожидание"
    COOKING = "готовка"
    READY = "готово"
    COMPLETED = "выполнено"


class OrderSystem:
    def __init__(self):
        # ресторан открыт
        self.kitchen_ready = threading.Event()


        self.stove_condition = threading.Condition()
        self.available_stoves = 2

        # очередь заказов
        self.order_queue = queue.Queue(maxsize=10)

        # статистика
        self.stats = {
            "total_orders": 0,
            "completed_orders": 0,
            "failed_orders": 0,
            "cooking_time_total": 0
        }
        self.stats_lock = threading.Lock()

        # флаг работы системы
        self.system_running = False

        # потоки
        self.producers = []
        self.consumers = []
        self.monitor_thread = None

    # подготовка кухни к работе
    def kitchen_preparation(self):
        print("ПОВАР: Начинаю подготовку кухни...")

        # имитация подготовки
        tasks = [
            "Проверяю оборудование",
            "Настраиваю температуру плит",
            "Подготавливаю ингредиенты",
            "Запускаю вытяжку",
            "Натираю приборы"
        ]

        for task in tasks:
            print(f"ПОВАР: {task}")
            time.sleep(1)

        print("ПОВАР: Кухня готова! ОТКРЫВАЕМСЯ!")
        self.kitchen_ready.set()

    # функция для генерации заказов т.е. оффицианыт
    def order_producer(self, producer_id):
        menu_items = [
            "Пицца Маргарита", "Паста Карбонара", "Стейк Рибай", "Салат Цезарь", "Бургер Делишес", "Суп Том-Ям",
            "Тако с говядиной", "Греческий салат", "Суши Филадельфия", "Рамен с говядиной"
        ]

        while self.system_running:
            if not self.kitchen_ready.wait(timeout=1):
                continue

            order = {
                "order_id": random.randint(1000, 9999),
                "customer_id": random.randint(1, 100),
                "dish": random.choice(menu_items),
                "complexity": random.randint(1, 5),
                "status": OrderStatus.PENDING.value,
                "created_time": datetime.now(),
                "producer_id": producer_id
            }

            try:
                self.order_queue.put(order, timeout=1)
                print(f"ОФИЦИАНТ - {producer_id}, принял заказ {order['order_id']}")
                with self.stats_lock:
                    self.stats["total_orders"] += 1
            except queue.Full:
                continue

            time.sleep(random.uniform(0.5, 2))

    # обработка заказов через повара
    def chef_consumer(self, chef_id):
        while self.system_running:
            if not self.kitchen_ready.wait(timeout=1):
                continue

            # получаем заказ
            try:
                order = self.order_queue.get(timeout=1)
            except queue.Empty:
                continue

            order["status"] = OrderStatus.COOKING.value
            order["chef_id"] = chef_id
            start_cooking = datetime.now()

            # занимаем конфорку
            with self.stove_condition:
                while self.available_stoves == 0 and self.system_running:
                    self.stove_condition.wait(timeout=1)

                if not self.system_running:
                    self.order_queue.put(order)
                    break

                self.available_stoves -= 1

            if not self.system_running:
                break

            print(f"ПОВАР {chef_id}: Занял конфорку и начинаю готовить заказ №{order['order_id']}")

            # готовим заказ
            cooking_time = order["complexity"] * 0.5
            time.sleep(cooking_time)

            order["status"] = OrderStatus.READY.value
            end_cooking = datetime.now()

            print(f"ПОВАР {chef_id}: заказ №{order['order_id']} готов! Освобождаю конфорку...")

            with self.stove_condition:
                self.available_stoves += 1
                self.stove_condition.notify_all()

            with self.stats_lock:
                self.stats["completed_orders"] += 1
                self.stats["cooking_time_total"] += (end_cooking - start_cooking).total_seconds()

            self.order_queue.task_done()

    def monitoring(self):
        while self.system_running:
            time.sleep(5)
            if not self.kitchen_ready.wait(timeout=1):
                continue

            with self.stats_lock:
                total_orders = self.stats["total_orders"]
                completed_orders = self.stats["completed_orders"]
                cooking_time_total = self.stats["cooking_time_total"]

            average_time = (cooking_time_total / completed_orders) if completed_orders > 0 else 0

            in_queue = self.order_queue.qsize()

            with self.stove_condition:
                free_stoves = self.available_stoves

            timestamp = datetime.now().strftime("%H:%M:%S")
            log_mes = f"[{timestamp}] Всего заказов: {total_orders}, В очереди: {in_queue}, Среднее время: {average_time:.2f}, Свободные конфорки: {free_stoves}\n"

            with open('restaurant_logs.txt', 'a', encoding="utf-8") as f:
                f.write(log_mes)

            print(f"МОНИТОРИНГ: {log_mes.strip()}")

    def start_system(self):
        print("ЗАПУСК СИСТЕМЫ РЕСТОРАНА...")
        self.system_running = True

        preparation_thread = threading.Thread(target=self.kitchen_preparation)
        preparation_thread.start()
        preparation_thread.join()

        for i in range(3):
            producer_thread = threading.Thread(target=self.order_producer, args=(i + 1,))
            self.producers.append(producer_thread)
            producer_thread.start()

        for i in range(2):
            consumer_thread = threading.Thread(target=self.chef_consumer, args=(i + 1,))
            self.consumers.append(consumer_thread)
            consumer_thread.start()

        self.monitor_thread = threading.Thread(target=self.monitoring)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_system(self):
        print("ЗАКРЫТИЕ РЕСТОРАНА...")
        self.system_running = False

        with self.stove_condition:
            self.stove_condition.notify_all()

        for i in self.producers:
            i.join(timeout=2)

        for j in self.consumers:
            j.join(timeout=2)

        while not self.order_queue.empty():
            try:
                self.order_queue.get_nowait()
                self.order_queue.task_done()
            except queue.Empty:
                break

        with self.stats_lock:
            total_orders = self.stats["total_orders"]
            completed_orders = self.stats["completed_orders"]
            cooking_time_total = self.stats["cooking_time_total"]

        average_time = (cooking_time_total / completed_orders) if completed_orders > 0 else 0

        print("ИТОГИ РАБОЧЕГО ДНЯ:")
        print(f"Всего принято заказов: {total_orders}")
        print(f"Успешно выполнено: {completed_orders}")
        print(f"Среднее время приготовления: {average_time:.2f} сек")

        print("РЕСТОРАН ЗАКРЫТ!")


if __name__ == "__main__":
    restaurant = OrderSystem()

    try:
        restaurant.start_system()
        time.sleep(30)
        restaurant.stop_system()

    except KeyboardInterrupt:
        print("!ЭКСТРЕННОЕ ЗАКРЫТИЕ!")
        restaurant.stop_system()