def generate_sample_data():
    """Generuje listę odczytów napięcia z czujnika."""
    return [
        0.5,
        0.7,
        1.2,
        0.9,
        2.5,
        3.1,
        0.2,
        0.0,
        4.2,
        1.5,
        1.8,
        2.2,
        0.1,
        0.5,
        2.9,
        3.5,
        0.8,
        0.4,
        1.1,
        4.5,
    ]


def classify_voltage(voltage):
    """Klasyfikuje napięcie na poziomy: Low, Medium, High."""
    if voltage < 1.0:
        return "Low"
    if 1.0 <= voltage < 3.0:
        return "Medium"
    return "High"


def run_analysis(data):
    """Oblicza średnią dla każdej kategorii i zlicza wystąpienia.
    UWAGA: W tej funkcji znajduje się błąd logiczny.
    """
    results = {
        "All": {"sum": 0, "count": 0},
        "Low": {"sum": 0, "count": 0},
        "Medium": {"sum": 0, "count": 0},
        "High": {"sum": 0, "count": 0},
    }

    for i in range(len(data)):
        val = data[i]
        category = classify_voltage(val)

        results[category]["sum"] += val
        results[category]["count"] += 1

        results["All"]["sum"] += val
        results["All"]["count"] += 1

    final_report = {}
    for cat, stats in results.items():
        if stats["count"] > 0:
            final_report[cat] = round(stats["sum"] / stats["count"], 2)
        else:
            final_report[cat] = 0.0

    return final_report


def main() -> None:
    print("--- Rozpoczynanie analizy danych napięcia ---")

    sensor_data = generate_sample_data()
    print(f"Pobrano {len(sensor_data)} próbek.")

    report = run_analysis(sensor_data)

    print("\nRaport końcowy (Średnie napięcia):")
    for category, avg in report.items():
        print(f"Kategoria {category}: {avg}V")


if __name__ == "__main__":
    main()
