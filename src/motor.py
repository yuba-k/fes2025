import RPi.GPIO as GPIO
import time

class Motor():
    def __init__(self):

        self.duty = 30
        self.right_pwm = 13
        self.left_pwm = 26
        self.right_phase = 11
        self.left_phase = 19

        GPIO.setmode(GPIO.BCM)#setmodeでBCMを用いて指定することを宣言　#GPIOピン番号のこと！

        self.direction = "stop"

        self.setup_gpio()

        self.initialize_motors()

    def setup_gpio(self):
        GPIO.setup(self.right_pwm,GPIO.OUT)#PWM出力
        GPIO.setup(self.right_phase,GPIO.OUT)#デジタル出力
        GPIO.setup(self.left_pwm,GPIO.OUT)#PWM出力
        GPIO.setup(self.left_phase,GPIO.OUT)#デジタル出力

    def initialize_motors(self):
        self.right = GPIO.PWM(self.right_pwm,200)
        self.left = GPIO.PWM(self.left_pwm,200)
        self.right.start(0)
        self.left.start(0)

    def move(self,duty = None):
        while True:
            if duty == None:
                duty = self.duty
            print(f"モータcmd{self.direction}")
            self.adjust_duty_cycle(self.direction,duty)
            self.right.ChangeDutyCycle(self.right_duty)
            self.left.ChangeDutyCycle(self.left_duty)
            time.sleep(0.5)

    def adjust_duty_cycle(self,direction,duty):
        GPIO.output(self.right_phase,GPIO.LOW)
        GPIO.output(self.left_phase,GPIO.LOW)
        if direction == "forward":
            self.right_duty = duty * 1.0
            self.left_duty = duty
        elif direction == "right" or direction == "search":
            self.right_duty = duty * 0.6
            self.left_duty = duty
        elif direction == "left":
            self.right_duty = duty * 1.0
            self.left_duty = duty * 0.6
        elif direction == "back":
            self.right_duty = self.left_duty = duty
            GPIO.output(self.right_phase,GPIO.HIGH)
            GPIO.output(self.left_phase,GPIO.HIGH)
        else:
            self.right_duty = self.left_duty = 0
            self.right.ChangeDutyCycle(0)
            self.left.ChangeDutyCycle(0)
        
    def cleanup(self):
        GPIO.cleanup()

def main():
    motor = Motor()
    print("forward,right,left")
    try:
        while True:
            direction =input("direction:")
            motor.move(direction,3,100)
    except KeyboardInterrupt:
        motor.cleanup()

if __name__ == "__main__":
    main()
