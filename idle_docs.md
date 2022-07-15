# Misty idle skill and skill switching



## main function

In the main function we first initialize the robot, so we can send commands to it.

After initializing the robot, we start an infinite **while** loop (I refer to this as "main loop"). This loop is to keep the program alive and make skill switching possible. There's probably a better solution for this, but this is how it works for now.

## Skill switching

We have a **skill_finished** global variable and its value is True when we start the program. In the main loop, we keep checking its value and if it's True, we call the **init_variables_and_events()** and **start_idle_skill()** functions. These functions will initialize the variables and events used for the idle skill and start the skill. The value of **skill_finished** will be set to False, so the main loop won't keep trying to start the idle skill.

We also have a **start_external** variable. When its value is True, we attempt to start an external skill based on the **skill_to_start** variable's value. So when we start an external skill, we will set the **start_external** variable's value to True, and we set the **skill_to_start** variable's value to the name of the skill we want to start.

### Starting an external skill from the idle skill

When we want to start an external skill from the idle skill, we call the **start_external_skill()** function. We pass the name of the skill we want to start as a parameter. This function calls the **stop_idle_skill()** function which unregisters all events, stop any services used in the skill and stops misty's movement. We set the **skill_finished** variable's value to the skill name we got as a parameter.

~~~python
start_external_skill("sample")
~~~

Then we can call an external skill from the main loop, and we should set the skill_finished variable's value as the skills return value.

~~~python
if start_external:
        if skill_to_start == "sample":
                    skill_finished = sample_skill.start_sample_skill(misty)
~~~

### External skills

**Requirements:**

- external skills should be functions with an infinite loop (so we don't exit the skill immediately)
- they get the robot as a parameter, so we can send commands to it from the skill
- they need a way to exit the loop, so we can return to the idle skill
- they need to stop all events, services, movements etc. they're using after exiting the loop
- then they need to return **True**, so the while loop in the main program starts the idle skill again

sample_skill.py can be used as an example/starting point