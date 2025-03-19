---
permalink: /about/
title: "About"
---

I am a software engineer specializing in Linux kernel, bootloaders and embedded systems.

However I do not limit myself, so I worked on a lot of interesting stuff in my spare time

## [lima driver](https://docs.mesa3d.org/drivers/lima.html)

Disclaimer: I am just one of developers who worked on this driver

This is a reverse-engineered driver (as in there is no public documentation on this GPU) for ARM Mali 400/450 (Utgard), GLES2-class GPU from ~2008

I worked [a lot](https://gitlab.freedesktop.org/mesa/mesa/-/commits/main?author=Vasily%20Khoruzhick) on both command stream generation and on shader compilers (yes, compilers, Mali Utgard vertex shader and fragment shader have different ISA)


## libfprint drivers

I reverse-engineered protocols for a [lot of fingerprint scanners](https://gitlab.freedesktop.org/libfprint/libfprint/-/commits/master?author=Vasily%20Khoruzhick). I am not actively working on it anymore though.


## u-boot fixes and improvements

Bootloaders are fun. On most embedded platforms they are as close to the hardware as possible. [Click to see my contributions to u-boot](https://github.com/u-boot/u-boot/commits/master/?author=anarsoul) for various SoCs and boards. I mostly either add missing drivers/features for the hardware I have.

## Linux kernel patches

One of the reasons why I like Linux is that I [can fix it](https://web.git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/log/?qt=author&q=anarsoul) if it breaks

## Retro computers

I love retro-computers. I had a ZX-Spectrum clone what I was a kid, so I built a few clones for fun: Harlequin 128 rev. 2D and rev. 4B and [Sizif-512](https://github.com/UzixLS/zx-sizif-512)

So yeah, I know how to hold a soldering iron. I also dipped my toe in hardware development, I designed [DivMMC variant](https://anarsoul.github.io/divtiesus_maple/). It is a remake of original DivTiesus, I redid whole project in KiCAD, rerouted the PCB and added joystick and WiFi support. It is CPLD-based design, so it allowed me to tinker with Verilog

## Microcontrollers

And more reverse-engineering! Did you know that you can write ESP32 apps in Rust? See my [project](https://github.com/anarsoul/esp-rf-ook) to receive 433MHz OOK-modulated signal
