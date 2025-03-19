---
# layout: post
title:  "Running mainline Armbian on BTT CB1 and CB2"
date:   2025-03-19 20:52:00 -0700
categories:
 - blog
tags:
 - 3dprinters
 - armbian
 - cb1
 - cb2
 - btt
toc: true
---

*Disclaimer: this is **not** step-by-step tutorial. Please use your common sense when using my config/code snippets on your system*

Initially I planned this post to be a small cheatsheet on configuring Armbian for running Klipper, but instead it turned out to explain behind the scene work on a one-liner patch. Well, I hope it would entertain a reader :)

# 3D Printing!

Last year I've finally got into 3D printing.

First I bought Elegoo Neptune 4 Plus -- it's a large bed-slinger with Klipper-based firmware heavily modified by the vendor which I replaced with [OpenNep4une](https://github.com/OpenNeptune3D/OpenNept4une) (Armbian + mainline Klipper) within a few weeks.

![Neptune 4 Plus](/assets/images/neptune4plus.jpg)

To be honest, while OpenNept4une is better than Elegoo FW, yet it cannot make Neptune 4 Plus completely reliable, mostly due to its size and crappy proximity sensor (up to 0.1mm variance, but usually lower) that is used for bed levelling and as a Z-endstop. Thus I sold it, bought a Voron Trident kit from Formbot and built a Voron.

![My Voron](/assets/images/voron_trident.jpg)

Why Voron? Because it's open-source and all the components are off the shelf. And the community is amazing.

# Armbian on BTT CB1

Formbot kit comes with Manta M8P control board with BTT CB1 which is a CM4-formfactor SBC. CB1 is based on Allwinner H616 with 1G of RAM and no built-in storage (you have to use a microSD card) which is sufficient for basic Klipper usage, but can easily choke on streaming video from USB camera, FPS can drop down to 4-6 which is a bit annoying.

What is more annoying is that BTT has their own Armbian fork which back in September 2024 was shipped with ancient vendor kernel. A lot of CB1 users complain that they get TTC (timer too close) Klipper errors and the usual recommendation is to replace it with RPi CM4

However I have strong suspicion that TTC is caused by either vendor kernel doing something wrong, and moreover I am not a fan of RPi.

A quick check on Armbian site revealed that it is actually supported by mainline Armbian (with a pretty recent kernel!), which is not very surprising assuming Allwinner H616 is well supported by the mainline kernel (kudos to linux-sunxi community!). Image can be found [here](https://www.armbian.com/bigtreetech-cb1/)

So I switched to mainline image for CB1. Installing Klipper is easy with [KIAUH](https://github.com/dw-0/kiauh)

Just a few more tweaks are needed

## Disable IPv6

I usually disable IPv6 on my appliances out of security concerns. With IPv6 enabled the device would get a public IPv6 address and will be reachable over internet which is not desirable. It can be done with `nmtui` (NetworkManager TUI) from console

## CAN0 interface TX queue length

can0 interface needs its TX queue length to be changed to 128 as per Klipper recommendations. It is easy to do with an udev rule, just create `/etc/udev/rules.d/99-can0.rules` with following contents:

```
SUBSYSTEM=="net", ACTION=="change", KERNEL=="can0"  ATTR{tx_queue_len}="128"
SUBSYSTEM=="net", ACTION=="add", KERNEL=="can0"  ATTR{tx_queue_len}="128"
```

## CPU frequency

Default cpufreq governor is `ondemand`, and it means that CPU will be idling at low frequency. It is suboptimial since switching from 408MHz to a higher frequency has a latency. In theory short bursts of CPU load when it runs at low frequency can cause TTC (timer too close) errors with Klipper. I didn't do any measurements, so don't take my word for it. Fortunately, Armbian has `cpufrequtils` package, so just install it with `sudo apt install cpufrequtils` and change its config at `/etc/default/cpufrequtils`. I just change MIN_SPEED here, for CB1 I set it to `792000` (and for CB2 `816000`). So on CB1 the file would look like this:

```
ENABLE=
MIN_SPEED=792000
MAX_SPEED=1512000
GOVERNOR=ondemand
```

## Bring can0 interface up on boot

Klipper expects can0 interface to be up, otherwise it won't start. It is easy to achieve with systemd-networkd, just create `/etc/systemd/network/80-can.network` with following contents:

```
[Match]
Name=can0

[CAN]
BitRate=1000K
RestartSec=100ms
```

And then just run `sudo systemctl enable systemd-networkd`

That is pretty much it for CB1, and I've been using CB1 without any problems for half a year. Well, I've got a TTC *once*, but it's after ~200h of printing

# Armbian on BTT CB2

Then I got bored and I decided to upgrade to CB2, which uses more powerful Rockchip RK3566, has 2G of RAM and 32G eMMC (yay for the faster storage!)

RK3566 is well supported in upstream kernel, so I hoped that there would be no issues with CB2. To be fair, I wasn't *very* wrong, it took a single night (or rather ~4h) to get it working just as well as CB1 (or rather better. I don't know yet, I just ran a simple ~45min print and it didn't fail)

## Building Armbian image

The first issue is that as of today I cannot point you to a prebuilt Armbian image for CB2 (I'm not even going to mention vendor's image...). It just doesn't exist yet, since CB2 support was just recently merged into upstream Armbian.

Fortunately, it is not difficult to build it. You just have to have docker running on your system, then clone their [build](https://github.com/armbian/build) repo and run `./compile.sh`. It will pull all the necessary container images and run the build in container (so far I'm happy with Armbian build experience. Kudos to Armbian team)

I built an image, dd'd it to microSD, connected CB2 to my BTT Pi4 adapter and booted it. Success! It worked on first boot, so I configured the system with a monitor and USB keyboard connected (I could do it with a serial adapter as well, but I was lazy) and decided to swap CB1 on my Manta with CB2.

## Fixing BTT HDMI5 compatibility issue

First boot on Manta - and nothing on screen. But I could ping the board and ssh into it. Well, at least it's not dead.

![BTT HDMI5](/assets/images/btt_hdmi5.jpg)

See the screen on the picture above? It is called BTT HDMI5 and is connected over HDMI. It has rather low resolution - 800x480 and thus pretty low pixel clock (33.3MHz as I figured out later). So why it doesn't work? Let's add `drm.debug=0xff` to the kernel arguments to figure that out. You can do that by editing `/boot/armbianEnv.txt` and adding `drm.debug=0xff` to extraargs. In my case, the line with `extraargs` now looks like:

```
extraargs=cma=256M drm.debug=0xff
```

Reboot and examine `dmesg` output. Interesting part is:

```
[    5.306141] rockchip-drm display-subsystem: [drm:drm_mode_prune_invalid] Rejected mode: "800x480": 68 33300 800 840 888 928 480 493 496 525 0x48 0x5 (NOCLOCK)
[    5.306183] rockchip-drm display-subsystem: [drm:drm_mode_prune_invalid] Rejected mode: "800x480": 68 33300 800 840 888 928 480 493 496 525 0x40 0xa (NOCLOCK)
[    5.306214] rockchip-drm display-subsystem: [drm:drm_mode_prune_invalid] Rejected mode: "640x480": 60 25175 640 656 752 800 480 490 492 525 0x40 0xa (NOCLOCK)
[    5.306243] rockchip-drm display-subsystem: [drm:drm_mode_prune_invalid] Rejected mode: "640x480": 60 25175 640 656 752 800 480 490 492 525 0x40 0xa (NOCLOCK)
[    5.306272] rockchip-drm display-subsystem: [drm:drm_mode_prune_invalid] Rejected mode: "640x480": 60 25200 640 656 752 800 480 490 492 525 0x40 0xa (NOCLOCK)

```

Here the first number after resolution is screen refresh rate (68Hz for 800x480), second is dot clock in KHz, 33300KHz or 33.3MHz for 800x480

Which means that display driver didn't like any of the modes that the screen has in EDID. Why? Let's check the code.

See `linux/drivers/gpu/drm/rockchip/dw_hdmi-rockchip.c`, relevant part:

```
static enum drm_mode_status
dw_hdmi_rockchip_mode_valid(struct dw_hdmi *dw_hdmi, void *data,
			    const struct drm_display_info *info,
			    const struct drm_display_mode *mode)
...
	if (hdmi->ref_clk) {
		int rpclk = clk_round_rate(hdmi->ref_clk, pclk);

		if (rpclk < 0 || abs(rpclk - pclk) > pclk / 1000)
			return MODE_NOCLOCK;
	}
...
}
```

Which means that ref_clk wasn't able to provide necessary clock rate. Let's check which clock is that, see `linux/arch/arm64/boot/dts/rockchip/rk356x-base.dtsi`:

```
	hdmi: hdmi@fe0a0000 {
		compatible = "rockchip,rk3568-dw-hdmi";
		reg = <0x0 0xfe0a0000 0x0 0x20000>;
		interrupts = <GIC_SPI 45 IRQ_TYPE_LEVEL_HIGH>;
		clocks = <&cru PCLK_HDMI_HOST>,
			 <&cru CLK_HDMI_SFR>,
			 <&cru CLK_HDMI_CEC>,
			 <&pmucru CLK_HDMI_REF>,
			 <&cru HCLK_VO>;
		clock-names = "iahb", "isfr", "cec", "ref";
```

So "ref" clock is CLK_HDMI_REF, now let's check `linux/drivers/clk/rockchip/clk-rk3568.c`:

```
PNAME(clk_hdmi_ref_p)			= { "hpll", "hpll_ph0" };
```

Which means that clk_hdmi_ref is a mux which can be switched to either HPLL or HPLL_PH0. rk356x PLL driver written in a way that it can only be configured to a list of pre-defined rates, and the settings for all fractional PLLs are in `rk3568_pll_rates` which doesn't have 33.3MHz (or 25.175MHz or 25.2MHz...). So let's just add an entry with necessary rate! 10 minutes with a datasheet and I came up with:

```
RK3036_PLL_RATE(33300000, 4, 111, 5, 4, 1, 0),
```

Where 33300000 is rate in Hz, 4 is _refdiv, 111 is _fbdiv, 5 is _postdiv1, 4 is _postdiv2. The rest is irrelevant, and final PLL rate can be calculated with following equation: `((24 MHz / _refdiv) * _fbdiv) / (_postdiv1 * _postdiv2)`

I created a patch (`git format-patch HEAD~1`), added it to `armbian-build/patch/kernel/archive/rockchip64-6.12`, rebuilt the image and installed a kernel image deb onto my board

Reboot - and voila - we have a working screen! The patch is already [submitted](https://patchwork.kernel.org/project/linux-rockchip/patch/20250318181930.1178256-1-anarsoul@gmail.com/) upstream and in [Armbian](https://github.com/armbian/build/pull/7970)

Don't forget to remove `drm.debug=0xff` from kernel command line if you tried to follow my steps :)

## CPU frequency

While doing initial configuration I noticed that the system feels a bit sluggish, so let's check CPU frequency:

```
# cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
cat: /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq: No such file or directory
```

`lscpu` doesn't list CPU frequency either.

Oops. Frequency scaling driver doesn't seem to be active. `dmesg` says:

```
platform cpufreq-dt: deferred probe pending: (reason unknown)
```

cpufreq-dt doesn't need much, and the usual reason why its probe is deferred is missing CPU voltage regulator driver.

Linux-6.12 didn't have CB2 device tree upstream, so Armbian ships its own that lives in `build/patch/kernel/archive/rockchip64-6.12/dt/rk3566-bigtreetech-pi2.dts`

Let's see what it says about CPU voltage regulator:

```
vdd_cpu: tsc4525@1c {
        compatible = "tcs,tcs452x";
...
```

Hmm, upstream device tree uses `tcs,tcs4525` for compatible string, and `linux/drivers/regulator/fan53555.c` doesn't seem to have `tcs,tcs452x`, but has `tcs,tcs4525`. That must be the reason, so [let's fix it](https://github.com/armbian/build/pull/7974)

And indeed, cpufreq is now working:

```
$ lscpu | grep MHz
CPU(s) scaling MHz:                   45%
CPU max MHz:                          1800.0000
CPU min MHz:                          408.0000
```

## Rotating the screen

After a few months of usage my BTT HDMI5 started showing artefacts in normal orientation, it is likely some electronics defect, but I noticed that it is vertical flip mode (press middle button to activate it). It is implemented in the screen firmware.

However it isn't very convenient to have image rotated by 180 degrees, is it? So let's rotate it again, but this time in software!

Change `extraargs` line in `/boot/armbianEnv.txt` to add `video=HDMI-A-1:panel_orientation=upside_down`. On my CB2 it now looks like this:

```
extraargs=cma=256M video=HDMI-A-1:panel_orientation=upside_down
```

(To be honest, I'm not sure why it needs 256M of CMA assuming the SoC has an IOMMU, but whatever)

Reboot and now the console (or boot logo if you enabled it) is correctly rotated, but once X11 for KlipperScreen is started, it is upside down again. Let's fix it for X11. Create `/etc/X11/xorg.conf.d/10-rotate-180.conf` with following contents:

```
Section "Monitor"
    Identifier "HDMI-1"
    Option "Rotate" "inverted"
EndSection


Section "InputClass"
            Identifier "Coordinate Transformation Matrix"
            MatchIsTouchscreen "on"
            MatchDevicePath "/dev/input/event*"
            MatchDriver "libinput"
            Option "CalibrationMatrix" "-1 0 1 0 -1 1 0 0 1"
EndSection
```

And restart KlipperScreen service: `sudo systemctl restart KlipperScreen`

Now firmware rotation is negated by software rotation and we have correct picture orientation.

That is pretty much it for CB2. All the changes I mentioned above are merged into Armbian, so if you built an image today you will have all the fixes
