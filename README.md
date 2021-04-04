# Arduinopydaqs

A function to read the EMG features and prosthetic commands from the Arduino (PEMG) system to the Axopy interface.
Mainly intended for internal use within [IntellSensing Lab] and [Edinburgh Neuroprosthetics].


Here is a minimal working example:

```python
from Arduinopydaqs.ArduinoPEMGdaq import ArduinoMKR_DAQ

daq = ArduinoMKR_DAQ(samples_per_read=1)
```


## Requirements
[Numpy](https://github.com/numpy/numpy) >= 1.11

[Axopy](https://github.com/intellsensing/axopy)

[pydaq](https://github.com/intellsensing/pydaqs)


## Hardware-specific package requirements
Tested versions in brackets.
* Arduino MKR ZERO (PEMG v2.2.x)
* Arduino MKR 1010 (PEMG v3.2.x)


## Notes
* Tested with Python >= 3.6
