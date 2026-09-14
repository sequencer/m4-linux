def probe_timer(utils):
    from m1n1.proxy import ProxyError

    report = {"register": "VM_TMR_FIQ_ENA_EL2", "read": False, "same_value_write": False}
    try:
        original = utils.mrs((3, 5, 15, 1, 3), call="el2")
        report.update(read=True, value=hex(original))
        utils.msr((3, 5, 15, 1, 3), original, call="el2")
        report["same_value_write"] = True
        if utils.mrs((3, 5, 15, 1, 3), call="el2") != original:
            raise ValueError("timer routing register changed after same-value write")
        report["readback_matches"] = True
    except (ProxyError, ValueError) as error:
        report["error"] = str(error)
    return report
