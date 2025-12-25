# ✅ Extract Invoice Number
        invoice_no = "Not found"
        match_inv = re.search(r'invoice\s*#?\s*(\d+)', text, re.I)
        if match_inv:
            invoice_no = match_inv.group(1)

        # ✅ Extract Total Amount
        total_amount = "Not found"
        match_total = re.search(r'total\s*\$?\s*([\d,.]+)', text, re.I)
        if match_total:
            total_amount = "$" + match_total.group(1)

        st.success("✅ Invoice processed successfully")
        st.write(f"**Invoice Number:** {invoice_no}")
        st.write(f"**Total Amount:** {total_amount}")

    except Exception as e:
        st.error("⚠️ OCR processing failed.")
        st.code(str(e))
        
