from bokeh.io import curdoc
from bokeh.layouts import row, widgetbox, column
from bokeh.models import ColumnDataSource, Span
from bokeh.models.widgets import Slider, Panel, Tabs
from bokeh.plotting import figure

import pandas as pd

#rectangle sizes for spike raster plot
rect_width = 0.003
rect_height = 0.7

#session names, for example 'mt_s1' is Monkey T, session 1
sessions = ['mm_s1', 'mt_s1', 'mt_s2', 'mt_s3']
session_exp_data = {} # session experiment data
all_session_plots = {}

# import data into dictionary
for name in sessions:
    session_data = dict()
    session_data['trials_info'] = pd.read_pickle('data/{}/trials_info.pickle'.format(name)) #includes trial data such as target locations
    session_data['cursor_pos'] = pd.read_pickle('data/{}/cursor_pos.pickle'.format(name)) # dataframe where each row is [time(1000Hz), x_pos, y_pos]
    session_data['pop_rate'] = pd.read_pickle('data/{}/f_rate.pickle'.format(name)) # dataframe where each row is [time(10Hz), population rate]
    session_data['burst_prob'] = pd.read_pickle('data/{}/burst_prob.pickle'.format(name)) # dataframe where each row is [time(10Hz), burst probability]
    session_data['spikes'] = pd.read_pickle('data/{}/spikes.pickle'.format(name)) # dataframe where each row is [time(1000Hz), neuron1_spike, neuron2_spike, neuron3_spike .....] ex [150, 0, 1, 0, 0, 0, 0, 1......] if 1, then neuron spiked during that time
    session_exp_data[name] = session_data

# listener for slider that updates time in experiment
def update_time(attrname, old, new):

    curr_session = sessions[tabs.active]

    # get plot objects
    curr_time_slider = all_session_plots[curr_session]['time_slider']
    curr_source_pos = all_session_plots[curr_session]['source_pos']
    curr_source_spikes = all_session_plots[curr_session]['source_spikes']
    curr_source_pop_rate = all_session_plots[curr_session]['source_pop_rate']
    curr_source_burst_prob = all_session_plots[curr_session]['source_burst_prob']
    curr_pop_rate_vline = all_session_plots[curr_session]['pop_rate_vline']
    curr_burst_vline = all_session_plots[curr_session]['burst_vline']
    curr_spike_raster_vline = all_session_plots[curr_session]['spike_raster_vline']

    # get plot info
    curr_pos_df = session_exp_data[curr_session]['cursor_pos']
    curr_rate_df = session_exp_data[curr_session]['pop_rate']
    curr_burst_df = session_exp_data[curr_session]['burst_prob']
    curr_spikes = session_exp_data[curr_session]['spikes']

    # Get the current slider values
    curr_time = curr_time_slider.value

    #update cursor position
    new_pos = {}
    x_pos = curr_pos_df.loc[curr_time]['x']
    y_pos = curr_pos_df.loc[curr_time]['y']
    new_pos['x'] = [x_pos, ]
    new_pos['y'] = [y_pos, ]
    curr_source_pos.data = new_pos

    # update population rate plot
    new_pop_rate = dict()
    new_pop_rate['x'] = curr_rate_df.loc[curr_time-2000:curr_time+2000].index.tolist()
    new_pop_rate['y'] = curr_rate_df.loc[curr_time-2000:curr_time+2000].tolist()
    curr_source_pop_rate.data = new_pop_rate

    #update burst probability plot
    new_burst_prob = dict()
    new_burst_prob['x'] = curr_burst_df.loc[curr_time-2000:curr_time+2000].index.tolist()
    new_burst_prob['y'] = curr_burst_df.loc[curr_time-2000:curr_time+2000].tolist()
    curr_source_burst_prob.data = new_burst_prob
    new_spike_raster = dict()

    # update spike raster plot
    all_units = []
    curr_spikes_in_range = curr_spikes.loc[curr_time-2000:curr_time+2000]
    for e, col in enumerate(curr_spikes_in_range.columns):
        unit_spikes = curr_spikes_in_range.iloc[:, e]
        unit_spikes = unit_spikes[unit_spikes == 1]
        all_units.append(unit_spikes * (e + 1))

    all_units_series = pd.concat(all_units)

    new_spike_raster['x'] = all_units_series.index
    new_spike_raster['y'] = all_units_series

    curr_source_spikes.data = new_spike_raster

    # update vertical lines on plots
    curr_pop_rate_vline.location = curr_time
    curr_burst_vline.location = curr_time
    curr_spike_raster_vline.location = curr_time


# listener for slider that updates trial #
def update_trial(attrname, old, new):
    curr_session = sessions[tabs.active]

    # get necessary data and plot objects
    curr_time_slider = all_session_plots[curr_session]['time_slider']
    curr_trials_slider = all_session_plots[curr_session]['trials_slider']
    curr_trials_info = session_exp_data[curr_session]['trials_info']
    curr_source_targets = all_session_plots[curr_session]['source_targets']

    trial_index = curr_trials_slider.value - 1

    curr_start_time = curr_trials_info.loc[trial_index, 'start']
    curr_end_time = curr_trials_info.loc[trial_index, 'end']

    # update current time slider to match experiment duration
    curr_time_slider.value = round(curr_start_time*1000)
    curr_time_slider.start = round(curr_start_time*1000)
    curr_time_slider.end = round(curr_end_time*1000)

    #update target positions
    new_targets = dict()

    target_x_cols = ['target1_x', 'target2_x', 'target3_x', 'target4_x']
    target_y_cols = ['target1_y', 'target2_y', 'target3_y', 'target4_y']
    target_x_list = curr_trials_info.loc[trial_index, target_x_cols].tolist()
    target_y_list = curr_trials_info.loc[trial_index, target_y_cols].tolist()

    new_targets['x'] = target_x_list
    new_targets['y'] = target_y_list

    curr_source_targets.data = new_targets


# plot initial data
for session_name in sessions:
    session_plot_data = {}
    curr_exp_data = session_exp_data[session_name]

    curr_pos_df = curr_exp_data['cursor_pos']
    curr_rate_df = curr_exp_data['pop_rate']
    curr_burst_df = curr_exp_data['burst_prob']
    curr_spikes = curr_exp_data['spikes']

    start_time = curr_exp_data['trials_info'].iloc[0]['start']
    start_time = int(1000*start_time)

    end_time = curr_exp_data['trials_info'].iloc[0]['end']
    end_time = int(1000 * end_time)

    num_trials = curr_exp_data['trials_info'].shape[0]

    all_units = []
    for e, col in enumerate(curr_spikes.columns):
        unit_spikes = curr_spikes.loc[start_time:end_time].iloc[:, e]
        unit_spikes = unit_spikes[unit_spikes == 1]
        all_units.append(unit_spikes * (e + 1))

    all_units_series = pd.concat(all_units)

    spike_raster_x = all_units_series.index
    spike_raster_y = all_units_series

    target_x_cols = ['target1_x', 'target2_x', 'target3_x', 'target4_x']
    target_y_cols = ['target1_y', 'target2_y', 'target3_y', 'target4_y']

    #initial target locations
    targets_x = curr_exp_data['trials_info'].iloc[0][target_x_cols].tolist()
    targets_y = curr_exp_data['trials_info'].iloc[0][target_y_cols].tolist()

    #initial cursor location
    cursor_x = curr_exp_data['cursor_pos'].loc[start_time]['x']
    cursor_y = curr_exp_data['cursor_pos'].loc[start_time]['y']

    #burst prob and firing rate timestamps and values

    ts_frate = curr_rate_df.loc[start_time - 2000:start_time + 2000].index.tolist()
    values_frate = curr_rate_df.loc[start_time - 2000:start_time + 2000].tolist()

    ts_burst = curr_burst_df.loc[start_time - 2000:start_time + 2000].index.tolist()
    values_burst = curr_burst_df.loc[start_time - 2000:start_time + 2000].tolist()

    # Set up data sources
    source_targets = ColumnDataSource(data=dict(x=targets_x, y=targets_y))
    source_pos = ColumnDataSource(data=dict(x=[cursor_x, ], y=[cursor_y, ]))
    source_pop_rate = ColumnDataSource(data=dict(x=ts_frate, y=values_frate))
    source_burst_prob = ColumnDataSource(data=dict(x=ts_burst, y=values_burst))
    source_spike_raster = ColumnDataSource(data=dict(x=spike_raster_x, y=spike_raster_y))

    # Set up plots
    plot_pos = figure(plot_height=500, plot_width=500, x_range=(-10, 10), y_range=(-10, 10))
    plot_spike_raster = figure(plot_height=200, plot_width=400, x_axis_label='time (ms)',
                             y_axis_label='Neuron #')
    plot_pop_rate = figure(plot_height=150, plot_width=400, x_axis_label='time (ms)', y_axis_label='Pop. Rate (Hz)')
    plot_burst_prob = figure(plot_height=150, plot_width=400, x_axis_label='time (ms)', y_axis_label='Burst Probability %')

    plot_pos.asterisk('x', 'y', size=10, color='red', source=source_pos)
    plot_pos.circle('x', 'y', size=24, alpha=0.4, source=source_targets)

    plot_pop_rate.line('x', 'y', source=source_pop_rate)
    pop_rate_vline = Span(location=start_time,
                         dimension='height', line_color='black',
                         line_dash='dotted', line_width=2, line_alpha=0.8)
    plot_pop_rate.add_layout(pop_rate_vline)

    plot_burst_prob.line('x', 'y', source=source_burst_prob)
    burst_vline = Span(location=start_time,
                         dimension='height', line_color='black',
                         line_dash='dotted', line_width=2, line_alpha=0.8)
    plot_burst_prob.add_layout(burst_vline)

    plot_spike_raster.rect('x', 'y', rect_width, rect_height, source=source_spike_raster)
    spike_raster_vline = Span(location=start_time,
                       dimension='height', line_color='black',
                       line_dash='dotted', line_width=2, line_alpha=0.8)
    plot_spike_raster.add_layout(spike_raster_vline)

    time_slider = Slider(title="time", value=start_time, start=start_time, end=end_time, step=100)
    trial_slider = Slider(title="Trial Number", value=1, start=1, end=num_trials, step=1)

    # Set up sliders
    time_box = widgetbox(time_slider)
    trial_box = widgetbox(trial_slider)
    time_slider.on_change('value', update_time)
    trial_slider.on_change('value', update_trial)

    # set up layouts
    plots = row(plot_pos, column(plot_spike_raster, plot_pop_rate, plot_burst_prob))
    session_plots = column(trial_box, plots, time_box)

    tab = Panel(child=session_plots, title=session_name)

    # store references of plot objects, for real time updating later
    session_plot_data['tab'] = tab
    session_plot_data['time_slider'] = time_slider
    session_plot_data['trials_slider'] = trial_slider
    session_plot_data['source_targets'] = source_targets
    session_plot_data['source_pos'] = source_pos
    session_plot_data['source_spikes'] = source_spike_raster
    session_plot_data['source_pop_rate'] = source_pop_rate
    session_plot_data['source_burst_prob'] = source_burst_prob
    session_plot_data['pop_rate_vline'] = pop_rate_vline
    session_plot_data['burst_vline'] = burst_vline
    session_plot_data['spike_raster_vline'] = spike_raster_vline

    all_session_plots[session_name] = session_plot_data

tabs_list = []

for name in all_session_plots.keys():
    tabs_list.append(all_session_plots[name]['tab'])
tabs = Tabs(tabs=tabs_list)

curdoc().add_root(tabs)
curdoc().title = "Macaque Reach Experiment"