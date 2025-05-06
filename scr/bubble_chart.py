import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from typing import Optional, List, Union

class BubbleChart:
    """A class for creating and visualizing bubble charts with collision detection."""
    
    def __init__(self, areas: Union[List[float], np.ndarray], bubble_spacing: float = 0):
        """Initialize the bubble chart with given areas and spacing.
        
        Args:
            areas: List or array of bubble areas
            bubble_spacing: Minimum spacing between bubbles (default: 0)
        """
        self._validate_input(areas, bubble_spacing)
        self._initialize_bubbles(areas, bubble_spacing)
        self._initialize_grid()
        self.com = self._calculate_center_of_mass()
    
    def _validate_input(self, areas: Union[List[float], np.ndarray], bubble_spacing: float):
        """Validate input parameters."""
        if not isinstance(bubble_spacing, (int, float)) or bubble_spacing < 0:
            raise ValueError("Bubble spacing must be a non-negative number")
        
        if len(areas) == 0:
            raise ValueError("Areas list cannot be empty")
    
    def _initialize_bubbles(self, areas: Union[List[float], np.ndarray], bubble_spacing: float):
        """Initialize bubble properties."""
        areas = np.asarray(areas, dtype=float)
        radii = np.sqrt(areas / np.pi)
        
        self.bubble_spacing = bubble_spacing
        self.bubbles = np.ones((len(areas), 4))  # [x, y, radius, area]
        self.bubbles[:, 2] = radii
        self.bubbles[:, 3] = areas
        
        self.max_step = 2 * self.bubbles[:, 2].max() + self.bubble_spacing
        self.step_dist = self.max_step / 2
    
    def _initialize_grid(self):
        """Initialize bubble positions in a grid layout."""
        length = np.ceil(np.sqrt(len(self.bubbles)))
        grid = np.arange(length) * self.max_step
        gx, gy = np.meshgrid(grid, grid)
        
        self.bubbles[:, 0] = gx.flatten()[:len(self.bubbles)]
        self.bubbles[:, 1] = gy.flatten()[:len(self.bubbles)]
    
    def _calculate_center_of_mass(self) -> np.ndarray:
        """Calculate the center of mass of all bubbles.
        
        Returns:
            Array with [x, y] coordinates of center of mass
        """
        return np.average(
            self.bubbles[:, :2], 
            axis=0, 
            weights=self.bubbles[:, 3]
        )
    
    def _calculate_center_distance(self, bubble: np.ndarray, bubbles: np.ndarray) -> np.ndarray:
        """Calculate distance between a bubble and all other bubbles.
        
        Args:
            bubble: Reference bubble [x, y, radius, area]
            bubbles: Array of other bubbles
            
        Returns:
            Array of distances
        """
        return np.hypot(bubble[0] - bubbles[:, 0], bubble[1] - bubbles[:, 1])
    
    def _calculate_outline_distance(self, bubble: np.ndarray, bubbles: np.ndarray) -> np.ndarray:
        """Calculate distance between bubble outlines.
        
        Args:
            bubble: Reference bubble [x, y, radius, area]
            bubbles: Array of other bubbles
            
        Returns:
            Array of outline distances
        """
        center_distance = self._calculate_center_distance(bubble, bubbles)
        return center_distance - bubble[2] - bubbles[:, 2] - self.bubble_spacing
    
    def _check_collisions(self, bubble: np.ndarray, bubbles: np.ndarray) -> int:
        """Count collisions between a bubble and others.
        
        Args:
            bubble: Reference bubble [x, y, radius, area]
            bubbles: Array of other bubbles
            
        Returns:
            Number of collisions
        """
        distance = self._calculate_outline_distance(bubble, bubbles)
        return len(distance[distance < 0])
    
    def _find_collisions(self, bubble: np.ndarray, bubbles: np.ndarray) -> List[int]:
        """Find indices of bubbles colliding with the reference bubble.
        
        Args:
            bubble: Reference bubble [x, y, radius, area]
            bubbles: Array of other bubbles
            
        Returns:
            List of indices of colliding bubbles
        """
        distance = self._calculate_outline_distance(bubble, bubbles)
        idx_min = np.argmin(distance)
        return [idx_min] if not isinstance(idx_min, np.ndarray) else idx_min.tolist()
    
    def collapse(self, n_iterations: int = 50, convergence_threshold: float = 0.1):
        """Optimize bubble positions to minimize collisions and center the chart.
        
        Args:
            n_iterations: Maximum number of iterations (default: 50)
            convergence_threshold: Movement threshold to reduce step size (default: 0.1)
        """
        for _ in range(n_iterations):
            moves = self._perform_iteration()
            
            # Reduce step size if movement has mostly converged
            if moves / len(self.bubbles) < convergence_threshold:
                self.step_dist /= 2
    
    def _perform_iteration(self) -> int:
        """Perform one iteration of the collapse algorithm.
        
        Returns:
            Number of bubbles that moved in this iteration
        """
        moves = 0
        
        for i in range(len(self.bubbles)):
            moves += self._adjust_bubble_position(i)
        
        return moves
    
    def _adjust_bubble_position(self, bubble_index: int) -> bool:
        """Adjust position of a single bubble to minimize collisions.
        
        Args:
            bubble_index: Index of bubble to adjust
            
        Returns:
            True if bubble moved, False otherwise
        """
        rest_bubbles = np.delete(self.bubbles, bubble_index, 0)
        moved = False
        
        # Try moving toward center of mass
        moved = self._try_move_toward_center(bubble_index, rest_bubbles)
        
        if not moved:
            # If that causes collisions, try moving orthogonally
            moved = self._try_move_orthogonal(bubble_index, rest_bubbles)
        
        return moved
    
    def _try_move_toward_center(self, bubble_index: int, rest_bubbles: np.ndarray) -> bool:
        """Attempt to move bubble toward center of mass.
        
        Args:
            bubble_index: Index of bubble to move
            rest_bubbles: Array of other bubbles
            
        Returns:
            True if move was successful (no collisions)
        """
        dir_vec = self.com - self.bubbles[bubble_index, :2]
        dir_vec /= np.linalg.norm(dir_vec)
        new_point = self.bubbles[bubble_index, :2] + dir_vec * self.step_dist
        new_bubble = np.append(new_point, self.bubbles[bubble_index, 2:4])
        
        if not self._check_collisions(new_bubble, rest_bubbles):
            self.bubbles[bubble_index, :] = new_bubble
            self.com = self._calculate_center_of_mass()
            return True
        return False
    
    def _try_move_orthogonal(self, bubble_index: int, rest_bubbles: np.ndarray) -> bool:
        """Attempt to move bubble orthogonally to avoid collisions.
        
        Args:
            bubble_index: Index of bubble to move
            rest_bubbles: Array of other bubbles
            
        Returns:
            True if move was successful (no collisions)
        """
        for colliding in self._find_collisions(self.bubbles[bubble_index], rest_bubbles):
            dir_vec = rest_bubbles[colliding, :2] - self.bubbles[bubble_index, :2]
            dir_vec /= np.linalg.norm(dir_vec)
            orth = np.array([dir_vec[1], -dir_vec[0]])
            
            # Try both orthogonal directions
            new_point1 = self.bubbles[bubble_index, :2] + orth * self.step_dist
            new_point2 = self.bubbles[bubble_index, :2] - orth * self.step_dist
            
            # Choose direction that moves closer to center
            dist1 = self._calculate_center_distance(self.com, np.array([new_point1]))
            dist2 = self._calculate_center_distance(self.com, np.array([new_point2]))
            new_point = new_point1 if dist1 < dist2 else new_point2
            
            new_bubble = np.append(new_point, self.bubbles[bubble_index, 2:4])
            
            if not self._check_collisions(new_bubble, rest_bubbles):
                self.bubbles[bubble_index, :] = new_bubble
                self.com = self._calculate_center_of_mass()
                return True
        return False
    
    def plot(self, ax: plt.Axes, labels: List[str], values: List[Union[int, float]], colors: List[str]):
        """Plot the bubble chart on the given axes.
        
        Args:
            ax: Matplotlib axes object
            labels: List of bubble labels
            values: List of bubble values
            colors: List of bubble colors
        """
        self._validate_plot_inputs(labels, values, colors)
        
        for i in range(len(self.bubbles)):
            self._plot_bubble(ax, i, labels[i], values[i], colors[i])
    
    def _validate_plot_inputs(self, labels: List[str], values: List[Union[int, float]], colors: List[str]):
        """Validate plot input parameters."""
        if len(labels) != len(self.bubbles) or len(values) != len(self.bubbles) or len(colors) != len(self.bubbles):
            raise ValueError("Labels, values, and colors must have same length as areas")
    
    def _plot_bubble(self, ax: plt.Axes, index: int, label: str, value: Union[int, float], color: str):
        """Plot a single bubble with label and value."""
        # Draw the bubble
        bubble = self.bubbles[index]
        circ = plt.Circle(bubble[:2], bubble[2], color=color)
        ax.add_patch(circ)
        
        # Calculate dynamic font size based on bubble size
        font_size = max(10, bubble[2] * 0.6)
        value_font_size = font_size * 0.7
        
        # Add label
        ax.text(bubble[0], bubble[1], label,
                ha='center', va='center', 
                fontsize=font_size)
        
        # Add value below label
        ax.text(bubble[0], bubble[1] - bubble[2] * 0.2, str(value),
                ha='center', va='center', 
                fontsize=value_font_size, 
                color='black')


class BubbleChartVisualizer:
    """A helper class for creating and saving bubble chart visualizations."""
    
    @staticmethod
    def create_bubble_chart(
        data: 'pd.DataFrame',
        areas_column: str,
        labels_column: str,
        values_column: str,
        colors_column: str,
        title: str = '',
        figsize: tuple = (10, 10),
        bubble_spacing: float = 0.47,
        save_path: Optional[str] = None,
        dpi: int = 600
    ) -> plt.Figure:
        """Create and optionally save a bubble chart visualization.
        
        Args:
            data: DataFrame containing the data
            areas_column: Name of column with area values
            labels_column: Name of column with label text
            values_column: Name of column with value text
            colors_column: Name of column with color values
            title: Chart title (default: '')
            figsize: Figure size (default: (10, 10))
            bubble_spacing: Spacing between bubbles (default: 0.47)
            save_path: Path to save image (default: None)
            dpi: DPI for saved image (default: 600)
            
        Returns:
            Matplotlib figure object
        """
        # Set up plot style
        plt.rcParams.update({
            'font.family': 'Candara',
            'font.style': 'normal',
            'font.size': 11
        })
        
        # Create and optimize bubble chart
        bubble_chart = BubbleChart(
            areas=data[areas_column], 
            bubble_spacing=bubble_spacing
        )
        bubble_chart.collapse()
        
        # Create figure and plot
        fig, ax = plt.subplots(
            subplot_kw=dict(aspect="equal"), 
            figsize=figsize
        )
        bubble_chart.plot(
            ax, 
            data[labels_column], 
            data[values_column], 
            data[colors_column]
        )
        
        # Format axes
        ax.axis("off")
        ax.relim()
        ax.autoscale_view()
        
        # Add title and credits
        if title:
            ax.set_title(title, fontweight='bold', fontsize=20)
        
        BubbleChartVisualizer._add_credits(ax)
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        # Save if requested
        if save_path:
            plt.savefig(save_path, dpi=dpi)
        
        return fig
    
    @staticmethod
    def _add_credits(ax: plt.Axes):
        """Add credits text to the chart (implementation omitted)."""
        pass 
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        left_footnote = "Plot by: Jabulente | Data Source: Dummy Dataset | Data-Driven Insights"
        right_footnote = f"Generated on: {current_time}"
        ax.text(0.01, -0.03, left_footnote, ha='left', va='center', fontsize=8, color='black', transform=ax.transAxes, fontweight='bold')
        ax.text(0.7, -0.03, right_footnote, ha='left', va='center', fontsize=8, color='black', transform=ax.transAxes, fontweight='bold')