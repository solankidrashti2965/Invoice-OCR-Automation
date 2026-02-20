    # ---------------- MONEY INTELLIGENCE ----------------
    amounts = re.findall(r'\d+\.\d{2}', clean_text)

    numeric_values = []

    for amt in amounts:
        try:
            value = float(amt)
            if value > 5:   # ignore tiny numbers
                numeric_values.append(value)
        except:
            continue

    if numeric_values:
        numeric_values = sorted(numeric_values)

        # Largest = Total
        total_value = numeric_values[-1]
        data["Total Amount"] = str(total_value)

        # If tax exists, calculate subtotal
        if data["Tax"] != "Not found":
            try:
                tax_value = float(data["Tax"])
                subtotal_value = round(total_value - tax_value, 2)
                data["Subtotal"] = str(subtotal_value)
            except:
                pass
        else:
            # fallback second largest
            if len(numeric_values) >= 2:
                data["Subtotal"] = str(numeric_values[-2])
