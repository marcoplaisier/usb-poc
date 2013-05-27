__author__ = 'marco'

import errno
import usb.core
import usb.util
import time


class usb_poc(object):
    """

    """

    def __init__(self):
        """Find the USB-device and put it in the right configuration.

        For this PoC we find the right USB device by its vendor and product id. This function will throw an error if
        the device is not found.
        This is a HID-device, which is usually claimed by the kernel. So, this function will first detach the kernel
        driver so we can read and write to the device.

        Up until this point, this is standard. However, every tutorial now makes a call to
        dev.set_configuration(interface_number) to put the device in a known configuration. I do not know precisely why,
        but this is not necessary. The device only has one configuration and no alternate configurations (see
        descriptors.txt)



        """
        vendor = 0xD59
        product = 0x8080

        try:
            self.dev = usb.core.find(idVendor=vendor, idProduct=product)  # returns None if device is not found
        except IOError as e:
            if e[0] == errno.PERM:
                e.msg = "You should be root to run this script"
                raise

        if self.dev is None:  # quit if we did not find the right USB device
            raise usb.core.USBError("Device not found. Is it connected?")

        if self.dev.is_kernel_driver_active(0):  # if the device is claimed by the kernel, we need to reclaim it
            self.dev.detach_kernel_driver(0)

    def run(self):
        """Main routine that reads in the pot and buttons and writes to the stepper motor and LEDs

        The LEDs consist of a simple counter up to 255. When we put it in the proper byte, it will light up te proper
        LEDs. This counter is managed by the buttons. Buttons 1 increases the counter, button 2 decreases it. When both
        buttons are pressed, the counter is reset to 0.
        The pot meter returns two bytes one for the low and one for the low part. This data is put into the stepper
        motor

        """
        led_state = 0
        read_end_point = 0x81  # found through lsusb for testing
        write_end_point = 0x01
        amount_of_bytes = 64
        interface = 0
        timeout = 100  # millisecond

        try:
            while True:
                time.sleep(0.01)

                data = self.dev.read(read_end_point, amount_of_bytes, interface, timeout)

                buttons = data[0]

                if buttons == 1:
                    led_state -= 1 if led_state > 0 else 0
                elif buttons == 2:
                    led_state += 1 if led_state < 255 else 255
                elif buttons == 3:
                    led_state = 0

                data[0], data[1], data[2] = data[1], data[2], led_state  # byte orderings do not match perfectly
                                                                         # nice python

                self.dev.write(write_end_point, data, interface, timeout)
        except KeyboardInterrupt as k:  # when we pushed CTRL-c
            self.dev.reset() # we will finish and clean up after our selves


if __name__ == "__main__":
    usb_poc().run()
