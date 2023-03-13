#!/usr/bin/env python3
from argparse import ArgumentParser
import depthai as dai
import subprocess
import os, signal
import re
from Qt import QtWidgets, QtCore
from .NodeGraphQt import NodeGraph, BaseNode, PropertiesBinWidget
from .NodeGraphQt.constants import ViewerEnum
import json
import time
from threading import Thread
from typing import Any, Dict, List
from .NodeGraphQt.trace_event import *

class DepthaiNode(BaseNode):
    # unique node identifier.
    __identifier__ = 'dai'

    # initial default node name.
    NODE_NAME = 'Node'

    def __init__(self):
        super(DepthaiNode, self).__init__()
        # create QLineEdit text input widget.
        # self.add_text_input('my_input', 'Text Input', tab='widgets')

class NodePort:
    id: str # Id of the port
    name: str # preview, out, video...
    port: Any = None  # QT port object
    node: Dict  # From json schema
    type: int  # Input or output
    dai_node: Any
    group_name: str
    blocking: bool
    queue_size: int

    def nice_name(self) -> str: # For visualization
        return f"{self.group_name}[{self.name}]" if self.group_name else self.name

    def create(self) -> bool:
        return self.port is None
    def is_input(self) -> bool:
        return self.type == 3

    def is_output(self) -> bool:
        return self.type == 0

    def find_node(self, node_id: int, group_name: str, port_name: str) -> bool:
        return self.name == port_name and self.dai_node['id'] == node_id and self.group_name == group_name

    def __str__(self):
        return f"{self.dai_node['name']}.{self.name} ({self.id})"


class PipelineGraph:

    node_color = {
        "ColorCamera": (241, 148, 138),
        "MonoCamera": (243, 243, 243),
        "ImageManip": (174, 214, 241),
        "VideoEncoder": (190, 190, 190),

        "NeuralNetwork": (171, 235, 198),
        "DetectionNetwork": (171, 235, 198),
        "MobileNetDetectionNetwork": (171, 235, 198),
        "MobileNetSpatialDetectionNetwork": (171, 235, 198),
        "YoloDetectionNetwork": (171, 235, 198),
        "YoloSpatialDetectionNetwork": (171, 235, 198),
        "SpatialDetectionNetwork": (171, 235, 198),

        "SPIIn": (242, 215, 213),
        "XLinkIn": (242, 215, 213),

        "SPIOut": (230, 176, 170),
        "XLinkOut": (230, 176, 170),

        "Script": (249, 231, 159),

        "StereoDepth": (215, 189, 226),
        "SpatialLocationCalculator": (215, 189, 226),

        "EdgeDetector": (248, 196, 113),
        "FeatureTracker": (248, 196, 113),
        "ObjectTracker": (248, 196, 113),
        "IMU": (248, 196, 113)
    }
    default_node_color = (190, 190, 190)  # For node types that does not appear in 'node_color'
    process = None
    links: Dict[str, Dict[str, Any]]

    def __init__(self):
        # handle SIGINT to make the app terminate on CTRL+C
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

        self.app = QtWidgets.QApplication(["DepthAI Pipeline Graph"])

        # create node graph controller.
        self.graph = NodeGraph()
        self.graph.set_background_color(255,255,255)
        self.graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_NONE.value)

        self.graph.register_node(DepthaiNode)

        # TODO: show node properties via properties bin widget
        self.properties_bin = PropertiesBinWidget(node_graph=self.graph)
        self.properties_bin.setWindowFlags(QtCore.Qt.Tool)

        # show the node properties bin widget when a node is double-clicked.
        def display_properties_bin(node):
            if not self.properties_bin.isVisible():
                for p in self.ports:
                    if p.node == node:
                        txt = json.dumps(p.dai_node, sort_keys=True, indent=4, separators=(',', ': '))
                        self.properties_bin.node_clicked(txt)
                        self.properties_bin.show()
                        return

        # wire function to "node_double_clicked" signal.
        self.graph.node_double_clicked.connect(display_properties_bin)

        # show the node graph widget.
        self.graph_widget = self.graph.widget
        self.graph_widget.resize(1100, 800)

    def cmd_tool(self, args):
        if args.action == "load":
            self.graph_widget.show()
            self.graph.load_session(args.json)
            self.graph.fit_to_selection()
            self.graph.set_zoom(-0.9)
            self.graph.clear_selection()
            self.graph.clear_undo_stack()
            self.app.exec_()

        else:
            if args.action == "run":
                os.environ["PYTHONUNBUFFERED"] = "1"
                os.environ["DEPTHAI_LEVEL"] = "trace"

                command = args.command.split()
                if args.use_variable_names:
                    # If command starts with "python", we remove it
                    if "python" in command[0]:
                        command.pop(0)

                    command = "python -m trace -t ".split() + command

                pipeline_create_re = f'.*:\s*(.*)\s*=\s*{args.pipeline_name}\.create.*'
                node_name = []
                self.process = subprocess.Popen(command, shell=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                schema_str = None
                record_output = "" # Save the output and print it in case something went wrong
                while True:
                    if self.process.poll() is not None: break
                    line = self.process.stdout.readline()
                    record_output += line
                    if args.verbose:
                        print(line.rstrip('\n'))
                    # we are looking for  a line:  ... [debug] Schema dump: {"connections":[{"node1Id":1...
                    match = re.match(r'.* Schema dump: (.*)', line)
                    if match:
                        schema_str = match.group(1)
                        print("Pipeline schema retrieved")
                        break
                        # TODO(themarpe) - expose "do kill" now
                        # # print(schema_str)
                        # if not args.do_not_kill:
                        #     print("Terminating program...")
                        #     process.terminate()
                    elif args.use_variable_names:
                        match = re.match(pipeline_create_re, line)
                        if match:
                            node_name.append(match.group(1))
                print("Program exited.")
                if schema_str is None:
                    if not args.verbose:
                        print(record_output)
                    print("\nSomething went wrong, the schema could not be extracted")
                    exit(1)
                schema = json.loads(schema_str)

            elif args.action == "from_file":
                with open(args.schema_file, "r") as schema_file:
                    # schema_file is either:
                    # 1) a Json file generated by a call to pipeline.serializeToJson(),
                    # 2) a log file generated by running the user program with DEPTHAI_LEVEL set to debug

                    # Are we in case 1) ?
                    try:
                        schema = json.load(schema_file)
                        if 'pipeline' not in schema:
                            print(f"Json file '{args.schema_file}' is missing 'pipeline' key")
                            exit(1)
                        schema = schema['pipeline']
                        print("Pipeline schema retrieved")
                    except json.decoder.JSONDecodeError:
                        # schema_file is not a Json file, so we are probably in case 2)
                        # we are looking for  a line:  ... [debug] Schema dump: {"connections":[{"node1Id":1...
                        schema_file.seek(0) # Rewind the file
                        while True:
                            line = schema_file.readline()
                            if len(line) == 0:
                                # End of file
                                print("\nSomething went wrong, the schema could not be extracted")
                                exit(1)
                            match = re.match(r'.* Schema dump: (.*)', line)
                            if match:
                                schema_str = match.group(1)
                                print("Pipeline schema retrieved")
                                break
                        schema = json.loads(schema_str)

            if args.verbose:
                print('Schema:', schema)

            self.create_graph(schema)

    def new_trace_log(self, msg: dai.LogMessage):
        self.new_trace_text(msg.payload)

    def new_trace_text(self, txt):
        # we are looking for  a line: EV:  ...
        match = re.search(r'EV:([0-9]+),S:([0-9]+),IDS:([0-9]+),IDD:([0-9]+),TSS:([0-9]+),TSN:([0-9]+)', txt.rstrip('\n'))
        if match:
            trace_event = TraceEvent()
            trace_event.event = EventEnum(int(match.group(1)))
            trace_event.status = StatusEnum(int(match.group(2)))
            trace_event.src_id = match.group(3)
            trace_event.dst_id = match.group(4)
            trace_event.timestamp = int(match.group(5)) + (int(match.group(6)) / 1000000000.0)
            trace_event.host_timestamp = time.time()

            if trace_event.status == StatusEnum.START and trace_event.event == EventEnum.SEND:
                link = self.links[trace_event.dst_id][trace_event.src_id]
                link.new_event(trace_event)
            elif trace_event.status == StatusEnum.END and trace_event.event == EventEnum.RECEIVE:
                for id, link in self.links[trace_event.src_id].items():
                    # SrcId is none, we can just take the first dst it
                    link.new_event(trace_event)
                    break


    def traceEventReader(self):
        # local_event_buffer = []
        while self.process.poll() is None:
            line = self.process.stdout.readline()
            self.new_trace_text(line)

    def create_graph(self, schema: Dict, device: dai.Device = None):

        dai_connections = schema['connections']

        self.ports: List[NodePort] = []
        start_nodes = []
        for n in schema['nodes']:
            dict_n = n[1]
            dict_n['ioInfo'] = [el[1] for el in dict_n['ioInfo']]

            node_name = dict_n['name']

            # Create the node
            qt_node = self.graph.create_node('dai.DepthaiNode',
                                             name=node_name,
                                             selected=False,
                                             color=self.node_color.get(node_name, self.default_node_color),
                                             text_color=(0,0,0),
                                             push_undo=False)

            if node_name in ['ColorCamera', 'MonoCamera', 'XLinkIn']:
                start_nodes.append(qt_node)

            # Alphabetic order
            ioInfo = list(sorted(dict_n['ioInfo'], key = lambda el: el['name']))

            for dict_io in ioInfo:
                p = NodePort()
                p.name = dict_io['name']
                p.type = dict_io['type'] # Input/Output
                p.node = qt_node
                p.dai_node = n[1]
                p.id = str(dict_io['id'])
                p.group_name = dict_io['group']
                p.blocking = dict_io['blocking']
                p.queue_size = dict_io['queueSize']
                self.ports.append(p)

        self.links = dict()
        for i, c in enumerate(dai_connections):
            src_node_id = c["node1Id"]
            src_name = c["node1Output"]
            src_group = c["node1OutputGroup"]
            dst_node_id = c["node2Id"]
            dst_name = c["node2Input"]
            dst_group = c["node2InputGroup"]

            src_port = [p for p in self.ports if p.find_node(src_node_id, src_group, src_name)][0]
            dst_port = [p for p in self.ports if p.find_node(dst_node_id, dst_group, dst_name)][0]

            if src_port.create():  # Output
                src_port.port = src_port.node.add_output(name=src_port.nice_name(), color=(50,50,255))
            if dst_port.create(): # Input
                port_color = (249, 75, 0) if dst_port.blocking else (0, 255, 0)
                port_label = f"[{dst_port.queue_size}] {dst_port.nice_name()}"
                dst_port.port = dst_port.node.add_input(name=port_label, color=port_color, multi_input=True)

            print(f"{i}. {src_port} -> {dst_port}")
            link = src_port.port.connect_to(dst_port.port, push_undo=False)

            if dst_port.id not in self.links:
                self.links[dst_port.id] = {}
            self.links[dst_port.id][src_port.id] = link

        # Lock the ports
        self.graph.lock_all_ports()

        self.graph_widget.show()
        self.graph.auto_layout_nodes(start_nodes=start_nodes)
        self.graph.fit_to_selection()
        self.graph.set_zoom(-0.9)
        self.graph.clear_selection()
        self.graph.clear_undo_stack()

        self.app.processEvents()
        self.graph.auto_layout_nodes()


        if self.process is not None: # Arg tool
            reading_thread = Thread(target=self.traceEventReader, args=())
            reading_thread.start()
        else:
            # device.setLogOutputLevel(dai.LogLevel.TRACE)
            device.setLogLevel(dai.LogLevel.TRACE)
            device.addLogCallback(self.new_trace_log)

    def update(self): # Called by main loop (on main Thread)
        for _, ports in self.links.items():
            for _, link in ports.items():
                link.update_fps() # Update text

        self.app.processEvents()

def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help="Action", required=True, dest="action")

    run_parser = subparsers.add_parser("run",
                                       help="Run your depthai program to create the corresponding pipeline graph")
    run_parser.add_argument('command', type=str,
                            help="The command with its arguments between ' or \" (ex: python script.py -i file)")
    run_parser.add_argument("-dnk", "--do_not_kill", action="store_true",
                            help="Don't terminate the command when the schema string has been retrieved")
    run_parser.add_argument("-var", "--use_variable_names", action="store_true",
                            help="Use the variable names from the python code to name the graph nodes")
    run_parser.add_argument("-p", "--pipeline_name", type=str, default="pipeline",
                            help="Name of the pipeline variable in the python code (default=%(default)s)")
    run_parser.add_argument('-v', '--verbose', action="store_true",
                            help="Show on the console the command output")

    from_file_parser = subparsers.add_parser("from_file",
                                             help="Create the pipeline graph by parsing a file containing the schema (log file generated with DEPTHAI_LEVEL=debug or Json file generated by pipeline.serializeToJSon())")
    from_file_parser.add_argument("schema_file",
                                  help="Path of the file containing the schema")

    load_parser = subparsers.add_parser("load", help="Load a previously saved pipeline graph")
    load_parser.add_argument("json_file",
                             help="Path of the .json file")
    args = parser.parse_args()

    p = PipelineGraph()
    p.cmd_tool(args)

    while True:
        p.update()
        time.sleep(0.001)

# Run as standalone tool
if __name__ == "__main__":
    main()
