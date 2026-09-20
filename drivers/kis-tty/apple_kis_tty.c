#include <linux/console.h>
#include <linux/device.h>
#include <linux/hrtimer.h>
#include <linux/io.h>
#include <linux/iopoll.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/serial_core.h>
#include <linux/tty_flip.h>

#define KIS_BASE 0x38812c000ULL
#define KIS_TX8 0x04
#define KIS_TX_FREE 0x14
#define KIS_RX8 0x1c
#define KIS_RX_COUNT 0x2c
#define KIS_POLL_NS 1000000

static struct uart_port kis_port;
static struct uart_driver kis_driver;
static struct device *kis_device;
static struct hrtimer kis_timer;
static bool kis_tx_enabled;
static bool kis_rx_enabled;
static bool kis_cread = true;
static unsigned int kis_fifo_size;

static void kis_transmit(struct uart_port *port)
{
	unsigned char character;

	uart_port_tx_limited(port, character, 256,
		readl(port->membase + KIS_TX_FREE),
		writel(character, port->membase + KIS_TX8), ({}));
}

static enum hrtimer_restart kis_poll(struct hrtimer *timer)
{
	struct uart_port *port = &kis_port;
	unsigned long flags;
	unsigned int budget = 256;
	bool received = false;

	uart_port_lock_irqsave(port, &flags);
	while (kis_rx_enabled && budget-- && readl(port->membase + KIS_RX_COUNT)) {
		unsigned char character = readl(port->membase + KIS_RX8) >> 8;

		port->icount.rx++;
		if (kis_cread) {
			if (!tty_insert_flip_char(&port->state->port, character, TTY_NORMAL))
				port->icount.buf_overrun++;
			received = true;
		}
	}
	if (kis_tx_enabled)
		kis_transmit(port);
	uart_port_unlock_irqrestore(port, flags);
	if (received)
		tty_flip_buffer_push(&port->state->port);
	hrtimer_forward_now(timer, ns_to_ktime(KIS_POLL_NS));
	return HRTIMER_RESTART;
}

static unsigned int kis_tx_empty(struct uart_port *port)
{
	return readl(port->membase + KIS_TX_FREE) >= kis_fifo_size ? TIOCSER_TEMT : 0;
}

static void kis_set_mctrl(struct uart_port *port, unsigned int mctrl)
{
}

static unsigned int kis_get_mctrl(struct uart_port *port)
{
	return TIOCM_CAR | TIOCM_CTS | TIOCM_DSR;
}

static void kis_stop_tx(struct uart_port *port)
{
	kis_tx_enabled = false;
}

static void kis_start_tx(struct uart_port *port)
{
	kis_tx_enabled = true;
	kis_transmit(port);
}

static void kis_stop_rx(struct uart_port *port)
{
	kis_rx_enabled = false;
}

static void kis_start_rx(struct uart_port *port)
{
	kis_rx_enabled = true;
}

static int kis_startup(struct uart_port *port)
{
	kis_rx_enabled = true;
	kis_tx_enabled = false;
	hrtimer_start(&kis_timer, ns_to_ktime(KIS_POLL_NS), HRTIMER_MODE_REL);
	return 0;
}

static void kis_shutdown(struct uart_port *port)
{
	hrtimer_cancel(&kis_timer);
	kis_rx_enabled = false;
	kis_tx_enabled = false;
}

static void kis_set_termios(struct uart_port *port, struct ktermios *termios,
			    const struct ktermios *old)
{
	unsigned long flags;

	termios->c_cflag &= ~(CSIZE | CSTOPB | PARENB | PARODD | CRTSCTS);
	termios->c_cflag |= CS8 | CLOCAL;
	tty_termios_encode_baud_rate(termios, 115200, 115200);
	uart_port_lock_irqsave(port, &flags);
	kis_cread = !!(termios->c_cflag & CREAD);
	uart_update_timeout(port, termios->c_cflag, 115200);
	uart_port_unlock_irqrestore(port, flags);
}

static const char *kis_type(struct uart_port *port)
{
	return "Apple KIS DockChannel";
}

static void kis_release_port(struct uart_port *port)
{
}

static int kis_request_port(struct uart_port *port)
{
	return 0;
}

static void kis_config_port(struct uart_port *port, int flags)
{
	if (flags & UART_CONFIG_TYPE)
		port->type = PORT_GENERIC;
}

static int kis_verify_port(struct uart_port *port, struct serial_struct *serial)
{
	return -EINVAL;
}

static const struct uart_ops kis_ops = {
	.tx_empty = kis_tx_empty,
	.set_mctrl = kis_set_mctrl,
	.get_mctrl = kis_get_mctrl,
	.stop_tx = kis_stop_tx,
	.start_tx = kis_start_tx,
	.stop_rx = kis_stop_rx,
	.start_rx = kis_start_rx,
	.startup = kis_startup,
	.shutdown = kis_shutdown,
	.set_termios = kis_set_termios,
	.type = kis_type,
	.release_port = kis_release_port,
	.request_port = kis_request_port,
	.config_port = kis_config_port,
	.verify_port = kis_verify_port,
};

static void kis_console_putchar(struct uart_port *port, unsigned char character)
{
	u32 available;

	if (!readl_poll_timeout_atomic(port->membase + KIS_TX_FREE,
				      available, available, 1, 1000))
		writel(character, port->membase + KIS_TX8);
}

static void kis_console_write(struct console *console, const char *text,
			      unsigned int count)
{
	unsigned long flags;
	bool locked;

	local_irq_save(flags);
	if (oops_in_progress)
		locked = uart_port_trylock(&kis_port);
	else {
		uart_port_lock(&kis_port);
		locked = true;
	}
	uart_console_write(&kis_port, text, count, kis_console_putchar);
	if (locked)
		uart_port_unlock(&kis_port);
	local_irq_restore(flags);
}

static int kis_console_setup(struct console *console, char *options)
{
	if (!kis_port.membase)
		return -ENODEV;
	console->index = 0;
	return uart_set_options(&kis_port, console, 115200, 'n', 8, 'n');
}

static struct console kis_console = {
	.name = "ttyKIS",
	.write = kis_console_write,
	.device = uart_console_device,
	.setup = kis_console_setup,
	.index = -1,
	.data = &kis_driver,
};

static struct uart_driver kis_driver = {
	.owner = THIS_MODULE,
	.driver_name = "apple-kis-tty",
	.dev_name = "ttyKIS",
	.nr = 1,
	.cons = &kis_console,
};

static int __init kis_init(void)
{
	int result;

	if (!of_machine_is_compatible("apple,j713"))
		return -ENODEV;
	kis_device = root_device_register("apple-kis-tty");
	if (IS_ERR(kis_device))
		return PTR_ERR(kis_device);
	kis_port.membase = ioremap(KIS_BASE, 0x100);
	if (!kis_port.membase) {
		result = -ENOMEM;
		goto unregister_device;
	}
	kis_fifo_size = 0x800;
	kis_port.mapbase = KIS_BASE;
	kis_port.iotype = UPIO_MEM32;
	kis_port.fifosize = kis_fifo_size;
	kis_port.uartclk = 115200 * 16;
	kis_port.flags = UPF_BOOT_AUTOCONF | UPF_FIXED_PORT;
	kis_port.ops = &kis_ops;
	kis_port.dev = kis_device;
	spin_lock_init(&kis_port.lock);
	hrtimer_setup(&kis_timer, kis_poll, CLOCK_MONOTONIC, HRTIMER_MODE_REL);
	result = uart_register_driver(&kis_driver);
	if (result)
		goto unmap;
	result = uart_add_one_port(&kis_driver, &kis_port);
	if (!result)
		return 0;
	uart_unregister_driver(&kis_driver);
unmap:
	iounmap(kis_port.membase);
unregister_device:
	root_device_unregister(kis_device);
	return result;
}

static void __exit kis_exit(void)
{
	uart_remove_one_port(&kis_driver, &kis_port);
	hrtimer_cancel(&kis_timer);
	uart_unregister_driver(&kis_driver);
	iounmap(kis_port.membase);
	root_device_unregister(kis_device);
}

module_init(kis_init);
module_exit(kis_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("M4 J713 KIS DockChannel polling TTY and console");
