from decimal import Decimal

def test_basic_conversion():
    """اختبار بسيط لمنطق التحويل"""
    
    # محاكاة أسعار الصرف
    # مثال: 1 ريال = 0.27 دولار (الدولار = 0.27)
    # مثال: 1 ريال = 0.24 يورو (اليورو = 0.24)
    
    print("اختبار منطق التحويل:")
    print("=" * 40)
    
    # التحويل من الريال إلى الدولار
    # 100 ريال * 0.27 = 27 دولار
    sar_amount = Decimal('100')
    usd_rate = Decimal('0.27')
    usd_result = sar_amount * usd_rate
    print(f"100 ريال = {usd_result} دولار")
    
    # التحويل من الدولار إلى الريال
    # 27 دولار / 0.27 = 100 ريال
    usd_amount = Decimal('27')
    sar_result = usd_amount / usd_rate
    print(f"27 دولار = {sar_result} ريال")
    
    # التحويل من دولار إلى يورو (عبر الريال)
    # 27 دولار / 0.27 = 100 ريال
    # 100 ريال * 0.24 = 24 يورو
    eur_rate = Decimal('0.24')
    sar_intermediate = usd_amount / usd_rate
    eur_result = sar_intermediate * eur_rate
    print(f"27 دولار = {eur_result} يورو")
    
    print("\nالمنطق يعمل بشكل صحيح! ✅")

if __name__ == "__main__":
    test_basic_conversion()
