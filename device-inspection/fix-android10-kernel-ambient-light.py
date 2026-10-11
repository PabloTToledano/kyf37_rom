"""Expose the KYF37 LV5216's real 16-level photosensor through a bounded read-only node."""
from pathlib import Path

path = Path('/home/pablo/kyf37-rom/kernel-android10/drivers/leds/leds-lv5216kc.c')
old = path.read_text()
anchor = 'static void lv5216_ctrl_update_alc_table('
code = '''/* KYF37_SENSOR_LEVEL: raw hardware level, deliberately not labelled lux. */
static ssize_t ambient_light_level_show(struct device *dev,
        struct device_attribute *attr, char *buf)
{
    struct led_classdev *cdev = dev_get_drvdata(dev);
    struct lv5216_led_data *led = container_of(cdev, struct lv5216_led_data, cdev);
    struct lv5216_data *data = led->parent;
    uint8_t raw;
    int ret;
    /* A separate reference preserves LCD/keypad automatic-light-control users. */
    mutex_lock(&data->control_lock);
    lv5216_photo_sensor_control(data, LED_TYPE_MAX, true);
    ret = lv5216_i2c_read(data->client, 0x15, &raw, 1);
    lv5216_photo_sensor_control(data, LED_TYPE_MAX, false);
    mutex_unlock(&data->control_lock);
    if (ret < 0)
        return ret;
    return scnprintf(buf, PAGE_SIZE, "%u\\n", raw >> 4);
}
static DEVICE_ATTR(ambient_light_level, 0444, ambient_light_level_show, NULL);

'''
new = old
if 'KYF37_SENSOR_LEVEL' not in new:
    assert new.count(anchor) == 1
    new = new.replace(anchor, code + anchor)
    anchor2 = '\t\t\tled->cdev_registered = true;'
    assert new.count(anchor2) == 1
    new = new.replace(anchor2, anchor2 + '''
            if (led->led_type == LED_TYPE_MLED) {
                err = device_create_file(led->cdev.dev, &dev_attr_ambient_light_level);
                if (err < 0)
                    LV5216_E_LOG("unable to expose ambient light level: %d", err);
            }''')
    # Remove the attribute before the backing LED device is unregistered.
    new = new.replace('led_classdev_unregister(&led->cdev);',
        'device_remove_file(led->cdev.dev, &dev_attr_ambient_light_level);\n\t\t\tled_classdev_unregister(&led->cdev);')
    path.write_text(new)
print('LV5216 read-only ambient_light_level (0..15), bounded sensor power reference staged')
