1. Install dependencies:
  sudo apt-get update && sudo apt-get install python3-dev cython3 -y

  2. Clone and build the library:
  git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
  cd rpi-rgb-led-matrix

  3. Build and install Python bindings:
  make build-python
  sudo make install-python

  4. When running your Python scripts, use these parameters:
  sudo python3 your_script.py --led-rows=32 --led-cols=64 --led-chain=2
  --led-gpio-mapping=adafruit-hat

  Key parameters for your setup:
  - --led-rows=32 (height of each panel)
  - --led-cols=64 (width of each panel)
  - --led-chain=2 (2 panels daisy chained)
  - --led-gpio-mapping=adafruit-hat (for Adafruit bonnet)
