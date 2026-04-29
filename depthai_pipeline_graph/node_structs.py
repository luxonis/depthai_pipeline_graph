from __future__ import annotations

from NodeGraphQt import BaseNode, NodeBaseWidget
from typing import Any, Dict, List
from Qt import QtWidgets, QtGui, QtCore

def draw_square_port(painter, rect, info):
    painter.save()

    color = QtGui.QColor(*info['color'])
    border_color = QtGui.QColor(*info['border_color'])

    pen = QtGui.QPen(border_color, 1.8)
    pen.setJoinStyle(QtCore.Qt.MiterJoin)

    painter.setPen(pen)
    painter.setBrush(color)
    painter.drawRect(rect)

    painter.restore()

def draw_circle_port(painter, rect, info):
    painter.save()

    color = QtGui.QColor(*info['color'])
    border_color = QtGui.QColor(*info['border_color'])

    pen = QtGui.QPen(border_color, 1.8)
    pen.setJoinStyle(QtCore.Qt.MiterJoin)

    painter.setPen(pen)
    painter.setBrush(color)
    painter.drawEllipse(rect)

    painter.restore()

class InfoTextWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(InfoTextWidget, self).__init__(parent)
        self.label = QtWidgets.QLabel(self)
        self.label.setText("(G:000ms,P:000ms,S:000ms,T:000ms)")
        self.label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.label)

class NodeWidgetWrapper(NodeBaseWidget):
    def __init__(self, parent=None):
        super(NodeWidgetWrapper, self).__init__(parent)
        self.set_name('info_widget')

        # set the label above the widget.
        self.set_label(' ')

        # set the custom widget.
        self.set_custom_widget(InfoTextWidget())

    def get_value(self):
        widget = self.get_custom_widget()
        return widget.label.text()

    def set_value(self, text):
        widget = self.get_custom_widget()
        widget.label.setText(text)

class NodeState:
    class QueueStats:
        maxQueued: int
        maxQueuedRecent: int
        medianQueuedRecent: int
        minQueuedRecent: int

    class State:
        IDLE = 0
        GETTING_INPUTS = 1
        PROCESSING = 2
        SENDING_OUTPUTS = 3

    class DurationStats:
        averageMicrosRecent: int
        maxMicros: int
        maxMicrosRecent: int
        medianMicrosRecent: int
        minMicros: int
        minMicrosRecent: int
        stdDevMicrosRecent: int

        def isValid(self) -> bool:
            return self.maxMicros > self.minMicros

    class Timing:
        durationStats: NodeState.DurationStats
        fps: float

    class InputQueueState:
        class State:
            IDLE = 0
            WAITING = 1
            BLOCKED = 2
        numQueued: int
        queueStats: NodeState.QueueStats
        state: NodeState.InputQueueState.State
        timing: NodeState.Timing

    class OutputQueueState:
        class State:
            IDLE = 0
            SENDING = 1
        state: NodeState.OutputQueueState.State
        timing: NodeState.Timing

    inputStates: dict[str, NodeState.InputQueueState]
    inputsGetTiming: NodeState.Timing
    mainLoopTiming: NodeState.Timing
    otherTimings: dict[str, NodeState.Timing]
    outputStates: dict[str, NodeState.OutputQueueState]
    outputsSendTiming: NodeState.Timing
    state: NodeState.State

    @staticmethod
    def fromJSON(json: dict) -> 'NodeState':
        ns = NodeState()

        mainLoopTimingData = json['mainLoopTiming']
        ns.mainLoopTiming = NodeState.Timing()
        ns.mainLoopTiming.fps = mainLoopTimingData['fps']

        mainLoopTsData = mainLoopTimingData['durationStats']
        mainLoopDurationStats = NodeState.DurationStats()
        mainLoopDurationStats.averageMicrosRecent = mainLoopTsData['averageMicrosRecent']
        mainLoopDurationStats.maxMicros = mainLoopTsData['maxMicros']
        mainLoopDurationStats.maxMicrosRecent = mainLoopTsData['maxMicrosRecent']
        mainLoopDurationStats.medianMicrosRecent = mainLoopTsData['medianMicrosRecent']
        mainLoopDurationStats.minMicros = mainLoopTsData['minMicros']
        mainLoopDurationStats.minMicrosRecent = mainLoopTsData['minMicrosRecent']
        mainLoopDurationStats.stdDevMicrosRecent = mainLoopTsData['stdDevMicrosRecent']
        ns.mainLoopTiming.durationStats = mainLoopDurationStats

        inputsGetTimingData = json['inputsGetTiming']
        ns.inputsGetTiming = NodeState.Timing()
        ns.inputsGetTiming.fps = inputsGetTimingData['fps']

        inputsGetTsData = inputsGetTimingData['durationStats']
        inputsGetDurationStats = NodeState.DurationStats()
        inputsGetDurationStats.averageMicrosRecent = inputsGetTsData['averageMicrosRecent']
        inputsGetDurationStats.maxMicros = inputsGetTsData['maxMicros']
        inputsGetDurationStats.maxMicrosRecent = inputsGetTsData['maxMicrosRecent']
        inputsGetDurationStats.medianMicrosRecent = inputsGetTsData['medianMicrosRecent']
        inputsGetDurationStats.minMicros = inputsGetTsData['minMicros']
        inputsGetDurationStats.minMicrosRecent = inputsGetTsData['minMicrosRecent']
        inputsGetDurationStats.stdDevMicrosRecent = inputsGetTsData['stdDevMicrosRecent']
        ns.inputsGetTiming.durationStats = inputsGetDurationStats

        outputsSendTimingData = json['outputsSendTiming']
        ns.outputsSendTiming = NodeState.Timing()
        ns.outputsSendTiming.fps = outputsSendTimingData['fps']

        outputsSendTsData = outputsSendTimingData['durationStats']
        outputsSendDurationStats = NodeState.DurationStats()
        outputsSendDurationStats.averageMicrosRecent = outputsSendTsData['averageMicrosRecent']
        outputsSendDurationStats.maxMicros = outputsSendTsData['maxMicros']
        outputsSendDurationStats.maxMicrosRecent = outputsSendTsData['maxMicrosRecent']
        outputsSendDurationStats.medianMicrosRecent = outputsSendTsData['medianMicrosRecent']
        outputsSendDurationStats.minMicros = outputsSendTsData['minMicros']
        outputsSendDurationStats.minMicrosRecent = outputsSendTsData['minMicrosRecent']
        outputsSendDurationStats.stdDevMicrosRecent = outputsSendTsData['stdDevMicrosRecent']
        ns.outputsSendTiming.durationStats = outputsSendDurationStats

        ns.inputStates = {}
        for inputName, inputStateData in json['inputStates'].items():
            inputState = NodeState.InputQueueState()
            inputState.numQueued = inputStateData['numQueued']

            qsData = inputStateData['queueStats']
            queueStats = NodeState.QueueStats()
            queueStats.maxQueued = qsData['maxQueued']
            queueStats.maxQueuedRecent = qsData['maxQueuedRecent']
            queueStats.medianQueuedRecent = qsData['medianQueuedRecent']
            queueStats.minQueuedRecent = qsData['minQueuedRecent']
            inputState.queueStats = queueStats

            inputState.state = inputStateData['state']

            timingData = inputStateData['timing']
            timing = NodeState.Timing()
            timing.fps = timingData['fps']

            tsData = timingData['durationStats']
            durationStats = NodeState.DurationStats()
            durationStats.averageMicrosRecent = tsData['averageMicrosRecent']
            durationStats.maxMicros = tsData['maxMicros']
            durationStats.maxMicrosRecent = tsData['maxMicrosRecent']
            durationStats.medianMicrosRecent = tsData['medianMicrosRecent']
            durationStats.minMicros = tsData['minMicros']
            durationStats.minMicrosRecent = tsData['minMicrosRecent']
            durationStats.stdDevMicrosRecent = tsData['stdDevMicrosRecent']
            timing.durationStats = durationStats

            inputState.timing = timing

            ns.inputStates[inputName] = inputState

        ns.outputStates = {}
        for outputName, outputStateData in json['outputStates'].items():
            outputState = NodeState.OutputQueueState()

            outputState.state = outputStateData['state']

            timingData = outputStateData['timing']
            timing = NodeState.Timing()
            timing.fps = timingData['fps']

            tsData = timingData['durationStats']
            durationStats = NodeState.DurationStats()
            durationStats.averageMicrosRecent = tsData['averageMicrosRecent']
            durationStats.maxMicros = tsData['maxMicros']
            durationStats.maxMicrosRecent = tsData['maxMicrosRecent']
            durationStats.medianMicrosRecent = tsData['medianMicrosRecent']
            durationStats.minMicros = tsData['minMicros']
            durationStats.minMicrosRecent = tsData['minMicrosRecent']
            durationStats.stdDevMicrosRecent = tsData['stdDevMicrosRecent']
            timing.durationStats = durationStats

            outputState.timing = timing

            ns.outputStates[outputName] = outputState

        ns.otherTimings = {}
        for otherName, otherTimingData in json['otherTimings'].items():
            otherTiming = NodeState.Timing()

            otherTiming.fps = otherTimingData['fps']

            tsData = otherTimingData['durationStats']
            durationStats = NodeState.DurationStats()
            durationStats.averageMicrosRecent = tsData['averageMicrosRecent']
            durationStats.maxMicros = tsData['maxMicros']
            durationStats.maxMicrosRecent = tsData['maxMicrosRecent']
            durationStats.medianMicrosRecent = tsData['medianMicrosRecent']
            durationStats.minMicros = tsData['minMicros']
            durationStats.minMicrosRecent = tsData['minMicrosRecent']
            durationStats.stdDevMicrosRecent = tsData['stdDevMicrosRecent']
            otherTiming.durationStats = durationStats

            ns.otherTimings[otherName] = otherTiming

        ns.state = json['state']

        return ns

class PipelineState:
    nodeStates: dict[int, NodeState]

    @staticmethod
    def fromJSON(json: dict) -> 'PipelineState':
        ps = PipelineState()
        ps.nodeStates = {}
        for nodeId, nodeStateData in json['nodeStates']:
            ps.nodeStates[int(nodeId)] = NodeState.fromJSON(nodeStateData)
        return ps


class DepthaiNode(BaseNode):
    # unique node identifier.
    __identifier__ = 'dai'

    # initial default node name.
    NODE_NAME = 'Node'

    def __init__(self):
        super(DepthaiNode, self).__init__()
        self.original_name = None
        self.state: NodeState | None = None
        self.updated = False
        self.update_node_state = False
        self.out_ports: List[NodePort] = []
        self.in_ports: List[NodePort] = []

        # add custom widget to node with "node.view" as the parent.
        node_widget = NodeWidgetWrapper(self.view)
        self.add_custom_widget(node_widget, tab='Info')

    def new_state(self, new_state: NodeState):
        self.state = new_state
        self.update_node_state = True

    def _fmt_timing_html(self, label, timing):
        """Render a Timing struct as an HTML row block: label, fps, durationStats."""
        if not timing or not timing.durationStats:
            return f"<b>{label}</b>: (no data)"
        ds = timing.durationStats
        if not ds.isValid():
            return f"<b>{label}</b>: (no samples yet)"
        return (
            f"<b>{label}</b>: fps={timing.fps:.2f}<br>"
            f"&nbsp;&nbsp;avg={ds.averageMicrosRecent}us, "
            f"median={ds.medianMicrosRecent}us, "
            f"stddev={ds.stdDevMicrosRecent}us<br>"
            f"&nbsp;&nbsp;min={ds.minMicrosRecent}us, "
            f"max={ds.maxMicrosRecent}us "
            f"(lifetime min/max={ds.minMicros}/{ds.maxMicros}us)"
        )

    def _build_node_tooltip(self):
        """Compose a full per-node tooltip with state, all timings, and the
        period-vs-active gap (idle/wait time hidden from instrumentation)."""
        if not self.state:
            return ""
        state_name = {0: "IDLE", 1: "GETTING_INPUTS", 2: "PROCESSING", 3: "SENDING_OUTPUTS"}.get(self.state.state, "?")
        ml = self.state.mainLoopTiming
        period_us = (1e6 / ml.fps) if ml.fps > 0 else 0
        active_us = ml.durationStats.averageMicrosRecent if (ml.durationStats and ml.durationStats.isValid()) else 0
        idle_us = max(0, period_us - active_us) if period_us > 0 else 0
        idle_pct = (100.0 * idle_us / period_us) if period_us > 0 else 0
        parts = [
            f"<b>{self.original_name or self.NODE_NAME}</b>",
            f"state: <b>{state_name}</b>",
            "",
            f"period (1/fps): {period_us:.0f}us",
            f"active (T): {active_us}us",
            f"<i>idle/wait: {idle_us:.0f}us ({idle_pct:.0f}% - sensor sync, blocked sends, etc; not in any bucket)</i>",
            "",
            self._fmt_timing_html("mainLoopTiming", ml),
            self._fmt_timing_html("inputsGetTiming", self.state.inputsGetTiming),
            self._fmt_timing_html("outputsSendTiming", self.state.outputsSendTiming),
        ]
        if self.state.otherTimings:
            parts.append("")
            parts.append("<b>otherTimings:</b>")
            for name, timing in self.state.otherTimings.items():
                parts.append(self._fmt_timing_html(f"&nbsp;&nbsp;{name}", timing))
        return "<br>".join(parts)

    def _build_input_port_tooltip(self, name, input_state, matching_port):
        in_state_name = {0: "IDLE", 1: "WAITING", 2: "BLOCKED"}.get(input_state.state, "?")
        parts = [
            f"<b>input port: {matching_port.nice_name()}</b>",
            f"group: {matching_port.group_name or '(none)'}",
            f"blocking: <b>{matching_port.blocking}</b> (waits on full queue if true, drops if false)",
            f"queue: {input_state.numQueued}/{matching_port.queue_size}",
            f"state: <b>{in_state_name}</b>",
            "",
            self._fmt_timing_html("port timing (recv)", input_state.timing),
        ]
        if input_state.queueStats:
            qs = input_state.queueStats
            parts.append(f"<b>queue stats</b>: max={qs.maxQueued}, recent max={qs.maxQueuedRecent}, recent median={qs.medianQueuedRecent}")
        return "<br>".join(parts)

    def _build_output_port_tooltip(self, name, output_state, matching_port):
        out_state_name = {0: "IDLE", 1: "SENDING"}.get(output_state.state, "?")
        send_fps = self.state.outputsSendTiming.fps if self.state else 0.0
        port_fps = output_state.timing.fps
        drop_fps = max(0.0, send_fps - port_fps)
        parts = [
            f"<b>output port: {matching_port.nice_name()}</b>",
            f"group: {matching_port.group_name or '(none)'}",
            f"blocking: <b>{matching_port.blocking}</b> (waits on full queue if true, drops if false)",
            f"state: <b>{out_state_name}</b>",
            "",
            f"send rate (node-level outputsSendTiming.fps): {send_fps:.2f}",
            f"per-port flow rate (this output's timing.fps): {port_fps:.2f}",
            f"<b>estimated drops</b>: {drop_fps:.2f} fps",
            "",
            self._fmt_timing_html("port timing (send)", output_state.timing),
        ]
        return "<br>".join(parts)

    def update_state(self):
        if self.original_name is None:
            self.original_name = self.NODE_NAME

        if not self.get_widget('info_widget').isVisible():
            return

        if self.state and self.update_node_state:
            self.update_node_state = False

            new_name = self.original_name
            if self.state.state == NodeState.State.GETTING_INPUTS:
                new_name += "[G]"
            elif self.state.state == NodeState.State.PROCESSING:
                new_name += "[P]"
            elif self.state.state == NodeState.State.SENDING_OUTPUTS:
                new_name += "[S]"

            if(self.name() != new_name):
                self.set_name(new_name)

            # Convert to ms
            t_to_get = self.state.inputsGetTiming.durationStats
            t_to_send = self.state.outputsSendTiming.durationStats
            t_total = self.state.mainLoopTiming.durationStats

            t_to_get_ms = (t_to_get.averageMicrosRecent if t_to_get.isValid() else 0) / 1000
            t_to_send_ms = (t_to_send.averageMicrosRecent if t_to_send.isValid() else 0) / 1000
            t_total_ms = (t_total.averageMicrosRecent if t_total.isValid() else 0) / 1000
            t_to_proc_ms = t_total_ms - t_to_get_ms - t_to_send_ms

            info_text = f"(G:{t_to_get_ms:03.0f}ms,P:{t_to_proc_ms:03.0f}ms,S:{t_to_send_ms:03.0f}ms,T:{t_total_ms:03.0f}ms)"
            widget = self.get_widget('info_widget')
            widget.set_value(info_text)

            # Rich tooltip on the node body so the user can hover for full
            # state detail (timings, period vs active, otherTimings).
            self.view.setToolTip(self._build_node_tooltip())

            for input_name, input_state in self.state.inputStates.items():
                matching_ports = [port for port in self.in_ports if port.name == input_name]
                if not matching_ports:
                    continue
                matching_port = matching_ports[0]
                port = self.get_input(matching_port.index)
                if port:
                    port_label = f"[{input_state.timing.fps: 3.1f} | {input_state.numQueued}/{matching_port.queue_size}] {matching_port.nice_name()}"
                    port.model.name = port_label
                    port.view.name = port_label
                    self.view.get_input_text_item(port.view).setPlainText(port_label)

                    if input_state.state == NodeState.InputQueueState.State.IDLE:
                        color = (34, 139, 34)  # green
                    elif input_state.state == NodeState.InputQueueState.State.WAITING:
                        color = (255, 255, 0)  # yellow
                    elif input_state.state == NodeState.InputQueueState.State.BLOCKED:
                        color = (255, 0, 0)  # red
                    else:
                        color = (204, 204, 204)

                    port.model.color = color
                    port_item = port.view
                    port_item.color = color
                    port_item.border_color = (204, 204, 204)
                    port_item.setToolTip(self._build_input_port_tooltip(input_name, input_state, matching_port))
                    port_item.update()

            for output_name, output_state in self.state.outputStates.items():
                matching_ports = [port for port in self.out_ports if port.name == output_name]
                if not matching_ports:
                    continue
                matching_port = matching_ports[0]
                port = self.get_output(matching_port.index)
                if port:
                    # Show node-level outputsSendTiming.fps - the rate at which
                    # this producer is pushing into the downstream queue. The
                    # per-input-port label on the consumer side shows the pull
                    # rate; the gap between them is the dropped-frame count.
                    # Blocking type is conveyed by red coloring on the consumer
                    # input port when it is BLOCKED.
                    send_fps = self.state.outputsSendTiming.fps
                    port_label = f"[{send_fps: 3.1f}] {matching_port.nice_name()}"
                    port.model.name = port_label
                    port.view.name = port_label
                    self.view.get_output_text_item(port.view).setPlainText(port_label)

                    if output_state.state == NodeState.OutputQueueState.State.IDLE:
                        color = (34, 139, 34)  # green
                    elif output_state.state == NodeState.OutputQueueState.State.SENDING:
                        color = (255, 255, 0)  # yellow
                    else:
                        color = (204, 204, 204)

                    port.model.color = color
                    port_item = port.view
                    port_item.color = color
                    port_item.border_color = (204, 204, 204)
                    port_item.setToolTip(self._build_output_port_tooltip(output_name, output_state, matching_port))
                    port_item.update()

            if not self.updated:
                self.updated = True
                self.update()
                self.view.draw_node()


class NodePort:
    TYPE_INPUT = 3
    TYPE_OUTPUT = 0

    id: str # Id of the port
    index: int  # Index of the port
    name: str # preview, out, video...
    port: Any = None  # QT port object
    node: Dict  # From json schema
    type: int  # Input or output
    dai_node: Any
    group_name: str
    blocking: bool
    queue_size: int
    state: NodeState.InputQueueState | NodeState.OutputQueueState | None

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
