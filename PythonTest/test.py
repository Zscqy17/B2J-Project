def onConnect(dat, peer):
    print("connect to BMI device succeed!")
    return

def onReceive(dat, rowIndex, message, bytes, peer):
    op("BMI_signal").par.value0=int(message)
    return

def onClose(dat, peer):
    print("BMI device disconnected!")
    return
