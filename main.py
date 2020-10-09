import click
import requests
import config
from tabulate import tabulate
import datetime
from json.decoder import JSONDecodeError

if config.DEBUG:
    BASE_URL = "http://127.0.0.1:5000/"
else:
    BASE_URL = "https://flex-dot-thesis-lock.ew.r.appspot.com/"


def provide_feedback(r, feedback_message=None):
    if r.status_code != 200:
        try:
            click.echo(r.json()["message"])
        except KeyError:
            click.echo(r.json()["msg"])
        except JSONDecodeError:
            click.echo("An unknown error occured: " + str(r.status_code))
    elif feedback_message:
        click.echo(feedback_message)
    else:
        click.echo("Your request was successful")

@click.group()
def cli():
    pass

@cli.command()
@click.argument('email-address')
@click.argument('password')
def create_admin_user(email_address, password):
    params = {'email_address': email_address, 'password': password}
    r = requests.post(BASE_URL + "create-admin-user/", json=params)
    provide_feedback(r)


@cli.command()
@click.argument('email-address')
def remove_user(email_address):
    url = BASE_URL + "users/{}/".format(email_address)
    r = requests.delete(url)
    provide_feedback(r)

@cli.command()
@click.argument('email-address')
@click.argument('rfid-id')
def assign_rfid_id_to_user(email_address, rfid_id):
    params = {'email_address': email_address, "rfid_id": rfid_id}
    r = requests.post(BASE_URL + "assign-rfid-id-to-user/", json=params)
    provide_feedback(r)

@cli.command()
@click.argument('email-address')
def remove_rfid_id_from_user(email_address):
    params = {'email_address': email_address}
    r = requests.post(BASE_URL + "remove-rfid-id-from-user/", json=params)
    provide_feedback(r)


@cli.command()
def view_all_users():
    url = BASE_URL + "users/"
    r = requests.get(url)
    provide_feedback(r, "")
    table = [["Email", "Is admin", "Access status", "RFID ID"]] + [[user["email_address"],
                                                         user["is_admin"], user["access_status"], user["rfid_id"]] for user in r.json()]
    click.echo(tabulate(table))

@cli.command()
@click.argument('email_address')
def view_user(email_address):
    """
    Access rules
    """
    url = BASE_URL + "users/{}/access-rules/".format(email_address)
    r = requests.get(url)
    provide_feedback(r, "")
    json = r.json()
    click.echo("Email address: " + json["email_address"])
    click.echo("Access rules:")
    click.echo("")
    table = [["Index", "Start", "End", "Until", "Frequency", "Count"]] + [[index, dt_block["start_dt"], dt_block["end_dt"],
                                                                           dt_block["until"], dt_block["frequency"], dt_block["count"]] for index, dt_block in enumerate(json["access_rules"])]
    click.echo(tabulate(table))


@cli.command()
def log():
    url = BASE_URL + "log/"
    r = requests.get(url)
    provide_feedback(r, "")

    json = r.json()
    table = [["Datetime", "Email address", "Method", "Category"]] + [[log["datetime"], log["user"], log["method"], log["category"]] for log in json["logs"]]
    click.echo(tabulate(table))

@cli.command('grant-unconditional-access')
@click.argument('email_address')
def grant_unconditional_access(email_address):
    """
    This will overule any
    access rules that may be present!
    """
    url = BASE_URL + "grant-unconditional-access/"
    r = requests.post(url, json={"email_address": email_address})
    provide_feedback(r, "")


@cli.command()
@click.argument('email_address')
def deny_unconditional_access(email_address):
    """
    This will overule any
    access rules that may be present!
    """
    url = BASE_URL + "deny-unconditional-access/"
    r = requests.post(url, json={"email_address": email_address})
    provide_feedback(r, "")


@cli.command()
@click.argument('email_address')
def use_access_rules(email_address):
    url = BASE_URL + "use-access-rules/"
    r = requests.post(url, json={"email_address": email_address})
    provide_feedback(r, "")


@cli.command('verify-rfid-id-access')
@click.argument('rfid-id')
def verify_rfid_id_access(rfid_id):
    url = BASE_URL + 'verify-rfid-id-access/'
    r =requests.post(url, json={'rfid_id': str(rfid_id)})
    provide_feedback(r)


@cli.command()
@click.argument('email_address')
@click.argument('start-dt-str')
@click.argument('end-dt-str')
@click.option('--until', default=None)
@click.option('--count', default=None, type=click.INT)
@click.option('--frequency', default=None, type=click.STRING)
def add_access_rule(email_address, start_dt_str: datetime.datetime, end_dt_str: datetime.datetime, until, count, frequency):

    start_dt = datetime.datetime.strptime(start_dt_str, "%Y/%m/%d %H:%M")
    end_dt = datetime.datetime.strptime(end_dt_str, "%Y/%m/%d %H:%M")

    start_dt_timestamp = start_dt.timestamp()
    end_dt_timestamp = end_dt.timestamp()

    rrulestr = ""

    if (count or until) and not frequency:
        click.Abort("Frequency required for RRule")

    if frequency:
        if frequency.upper() not in ["HOURLY", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"]:
            click.Abort(
                "Frequency should be HOURLY, DAILY, WEEKLY, MONTHLY, or YEARLY.")
        rrulestr += "FREQ={};".format(frequency.upper())

    if count:
        rrulestr += "COUNT={};".format(count)

    if until:
        dt = datetime.datetime.strptime(until, "%Y/%m/%d %H:%M")
        iso_dt_stamp = dt.strftime("%Y%m%dT%H%M%S")
        rrulestr += "UNTIL={};".format(iso_dt_stamp)

    payload = {"email_address": email_address, "start_dt_stamp": start_dt_timestamp,
               "end_dt_stamp": end_dt_timestamp, "rrule_str": rrulestr[:-1] if rrulestr else None}

    url = BASE_URL + "users/{}/access-rules/".format(email_address)
    r = requests.post(url, json=payload)
    provide_feedback(r, "")


@cli.command()
@click.argument('email_address', type=click.STRING)
@click.argument('index', type=click.INT)
def remove_access_rule(email_address, index):
    url = BASE_URL + "users/{}/access-rules/{}/".format(email_address, index)
    r = requests.delete(url)
    provide_feedback(r, "")


if __name__ == '__main__':
    cli()
