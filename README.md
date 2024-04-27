# ugly-alarm-clock
Turn an old clock radio into a modern marvel


config.txt - overwrite SD card version with the below after flashing but before first provisioning.
```
hdmi_cvt=480 320 60 1 0 0 0
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
avoid_warnings=1
disable_splash=1
dtoverlay=vc4-fkms-v3d
dtparam=i2c_arm=on
dtparam=spi=on
dtparam=audio=on
enable_uart=0
gpu_mem=256
```
Device variables:

FBCP_DISPLAY=adafruit-hx8357d-pitft

KIOSK=1

AUDIO_OUTPUT=RPI_HEADPHONES
