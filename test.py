import dns.resolver

def get_mx_records(domain):
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        mx_records = sorted([str(r.exchange).rstrip('.') for r in answers])
        return mx_records
    except Exception as e:
        return f"Error fetching MX records: {e}"

def check_duocode(domain):
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        for r in answers:
            txt_record = str(r).strip('"')
            print(txt_record)
            if "cisco" in txt_record.lower() or "duo" in txt_record.lower():
                return True
        return False
    except Exception as e:
        return f"Error checking TXT records: {e}"

def main():
    domain = input("Enter domain (e.g., example.com): ").strip()
    
    print(f"\nChecking email service for {domain}...")
    mx = get_mx_records(domain)
    print("MX Records / Email service:", mx)

    print("\nChecking for DuoCode security...")
    duocode_status = check_duocode(domain)
    if duocode_status is True:
        print("DuoCode security is enabled ✅")
    elif duocode_status is False:
        print("DuoCode security is NOT enabled ❌")
    else:
        print(duocode_status)

if __name__ == "__main__":
    main()
